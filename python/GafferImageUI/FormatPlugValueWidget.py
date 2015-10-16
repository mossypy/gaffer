##########################################################################
#
#  Copyright (c) 2012-2013, Image Engine Design Inc. All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are
#  met:
#
#      * Redistributions of source code must retain the above
#        copyright notice, this list of conditions and the following
#        disclaimer.
#
#      * Redistributions in binary form must reproduce the above
#        copyright notice, this list of conditions and the following
#        disclaimer in the documentation and/or other materials provided with
#        the distribution.
#
#      * Neither the name of John Haddon nor the names of
#        any other contributors to this software may be used to endorse or
#        promote products derived from this software without specific prior
#        written permission.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
#  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
#  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
#  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
#  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
#  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
#  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
#  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
#  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
#  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
##########################################################################

import functools

import IECore
import Gaffer
import GafferUI
import GafferImage

class FormatPlugValueWidget( GafferUI.PlugValueWidget ) :

	def __init__( self, plug, **kw ) :

		grid = GafferUI.GridContainer( spacing = 4 )
		GafferUI.PlugValueWidget.__init__( self, grid, plug, **kw )

		self.__menuButton = GafferUI.MenuButton( menu = GafferUI.Menu( Gaffer.WeakMethod( self.__menuDefinition ) ) )
		grid[0:2,0] = self.__menuButton

		if isinstance( plug, GafferImage.FormatPlug ) :

			self.__minLabel = GafferUI.Label( "Origin" )
			grid.addChild( self.__minLabel, index = ( 0, 1 ), alignment = ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ) )

			self.__minWidget = GafferUI.CompoundNumericPlugValueWidget( plug["displayWindow"]["min"] )
			grid[1,1] = self.__minWidget

			self.__maxLabel = GafferUI.Label( "Size" )
			grid.addChild( self.__maxLabel, index = ( 0, 2 ), alignment = ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ) )

			self.__maxWidget = GafferUI.CompoundNumericPlugValueWidget( plug["displayWindow"]["max"] )
			grid[1,2] = self.__maxWidget

			self.__pixelAspectLabel = GafferUI.Label( "Pixel Aspect" )
			grid.addChild( self.__pixelAspectLabel, index = ( 0, 3 ), alignment = ( GafferUI.HorizontalAlignment.Right, GafferUI.VerticalAlignment.Center ) )

			self.__pixelAspectWidget = GafferUI.NumericPlugValueWidget( plug["pixelAspect"] )
			grid[1,3] = self.__pixelAspectWidget

		self.__plugMetadataChangedConnection = Gaffer.Metadata.plugValueChangedSignal().connect( Gaffer.WeakMethod( self.__plugMetadataChanged ) )

		self._addPopupMenu( self.__menuButton )
		self._updateFromPlug()

	def setPlug( self, plug ) :

		self.__minWidget.setPlug( plug["displayWindow"]["min"] )
		self.__maxWidget.setPlug( plug["displayWindow"]["max"] )
		self.__pixelAspectWidget.setPlug( plug["pixelAspect"] )

		GafferUI.PlugValueWidget.setPlug( plug )

	def _updateFromPlug( self ) :

		self.__menuButton.setEnabled( self._editable() )

		text = ""
		mode = "standard"
		if self.getPlug() is not None :

			mode = Gaffer.Metadata.plugValue( self.getPlug(), "formatPlugValueWidget:mode" )
			with self.getContext() :
				fmt = self.getPlug().getValue()

			if fmt == GafferImage.Format() :
				text = "Default Format"
				# The empty display window of the default format is
				# confusing to look at, so turn off custom mode.
				mode = "standard"
			else :
				text = GafferImage.Format.name( fmt )
				if not text :
					# If the chosen format hasn't been registered,
					# force custom mode even if it hasn't been
					# asked for explicitly.
					mode = "custom"

		self.__menuButton.setText( text if mode != "custom" else "Custom" )

		for widget in ( self.__minLabel, self.__minWidget, self.__maxLabel, self.__maxWidget, self.__pixelAspectLabel, self.__pixelAspectWidget ) :
			widget.setVisible( mode == "custom" )

	def __menuDefinition( self ) :

		result = IECore.MenuDefinition()
		if self.getPlug() is None :
			return result

		formats = []
		if not self.getPlug().ancestor( Gaffer.ScriptNode ).isSame( self.getPlug().node() ) :
			formats.append( ( "Default Format", GafferImage.Format() ) )

		for name in GafferImage.Format.registeredFormats() :
			formats.append( ( name, GafferImage.Format.format( name ) ) )

		currentFormat = self.getPlug().getValue()
		modeIsCustom = Gaffer.Metadata.plugValue( self.getPlug(), "formatPlugValueWidget:mode" ) == "custom"
		for name, fmt in formats :
			result.append(
				"/" + name,
				{
					"command" : functools.partial( Gaffer.WeakMethod( self.__applyFormat ), fmt = fmt ),
					"checkBox" : fmt == currentFormat and not modeIsCustom,
				}
			)

		result.append( "/CustomDivider", { "divider" : True } )

		result.append(
			"/Custom",
			{
				"command" : Gaffer.WeakMethod( self.__applyCustomFormat ),
				"checkBox" : modeIsCustom or currentFormat not in [ f[1] for f in formats ],
			}
		)

		return result

	def __applyFormat( self, unused, fmt ) :

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :
			Gaffer.Metadata.registerPlugValue( self.getPlug(), "formatPlugValueWidget:mode", "standard", persistent = False )
			self.getPlug().setValue( fmt )

	def __applyCustomFormat( self, unused ) :

		with Gaffer.UndoContext( self.getPlug().ancestor( Gaffer.ScriptNode ) ) :

			with self.getContext() :
				if self.getPlug().getValue() == GafferImage.Format() :
					# Format is empty. It's kindof confusing to display that
					# to the user in the custom fields, so take the default
					# format and set it explicitly as a starting point for
					# editing.
					self.getPlug().setValue( GafferImage.FormatPlug.getDefaultFormat( self.getContext() ) )

			# When we first switch to custom mode, the current value will
			# actually be one of the registered formats. So we use this
			# metadata value to keep track of the user's desire to be in
			# custom mode despite of this fact. We use metadata rather than
			# a member variable so that undo will take us make to the non-custom
			# state automatically.
			Gaffer.Metadata.registerPlugValue( self.getPlug(), "formatPlugValueWidget:mode", "custom", persistent = False )

	def __plugMetadataChanged( self, nodeTypeId, plugPath, key, plug ) :

		if self.getPlug() is None or plug is None :
			return

		if not self.getPlug().isSame( plug ) :
			return

		if key == "formatPlugValueWidget:mode" :
			self._updateFromPlug()

GafferUI.PlugValueWidget.registerType( GafferImage.FormatPlug, FormatPlugValueWidget )
GafferUI.PlugValueWidget.registerType( GafferImage.AtomicFormatPlug, FormatPlugValueWidget )

