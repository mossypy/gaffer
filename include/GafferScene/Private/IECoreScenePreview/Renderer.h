//////////////////////////////////////////////////////////////////////////
//
//  Copyright (c) 2016, Image Engine Design Inc. All rights reserved.
//
//  Redistribution and use in source and binary forms, with or without
//  modification, are permitted provided that the following conditions are
//  met:
//
//      * Redistributions of source code must retain the above
//        copyright notice, this list of conditions and the following
//        disclaimer.
//
//      * Redistributions in binary form must reproduce the above
//        copyright notice, this list of conditions and the following
//        disclaimer in the documentation and/or other materials provided with
//        the distribution.
//
//      * Neither the name of John Haddon nor the names of
//        any other contributors to this software may be used to endorse or
//        promote products derived from this software without specific prior
//        written permission.
//
//  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
//  IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
//  THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
//  PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
//  CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
//  EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
//  PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
//  PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
//  LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
//  NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
//  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
//
//////////////////////////////////////////////////////////////////////////

#ifndef IECORESCENEPREVIEW_RENDERER_H
#define IECORESCENEPREVIEW_RENDERER_H

#include "IECore/CompoundObject.h"
#include "IECore/Display.h"

namespace IECoreScenePreview
{

/// \todo Derive from RunTimeTyped - we're just avoiding doing that
/// right now so we don't have to shuffle TypeIds between Gaffer and Cortex.
class Renderer : public IECore::RefCounted
{

	public :

		enum RenderType
		{
			/// Locations are emitted to the renderer immediately
			/// and not retained for later editing.
			Batch,
			/// Locations are retained, allowing interactive
			/// editing to be performed during rendering.
			Interactive,
			/// A scene description is serialised to file.
			SceneDescription
		};

		IE_CORE_DECLAREMEMBERPTR( Renderer )

		static const std::vector<IECore::InternedString> &types();
		/// Filename is only used if the renderType is SceneDescription.
		static Ptr create( const IECore::InternedString &type, RenderType renderType, const std::string &fileName = "" );

		/// \todo Rename Display->Output in Cortex.
		typedef IECore::Display Output;

		/// Sets a global option for the render. In interactive renders an option may
		/// be unset by passing a NULL value.
		///
		/// Standard Options
		/// ----------------
		///
		/// "camera", StringData, ""
		/// "resolution", V2iData, 1920x1080
		/// "pixelAspectRatio", FloatData, 1.0
		/// "cropWindow", Box2fData, ( ( 0, 0 ), ( 1, 1 ) )
		virtual void option( const IECore::InternedString &name, const IECore::Data *value ) = 0;
		/// Adds an output image to be rendered, In interactive renders an output may be
		/// removed by passing NULL as the value.
		virtual void output( const IECore::InternedString &name, const Output *output ) = 0;

		IE_CORE_FORWARDDECLARE( AttributesInterface );

		/// A handle to a block of attributes.
		class AttributesInterface : public IECore::RefCounted
		{

			public :

				IE_CORE_DECLAREMEMBERPTR( AttributesInterface );

			protected :

				virtual ~AttributesInterface();

		};

		/// Creates a bundle of attributes which can subsequently
		/// be assigned to objects with `ObjectInterface->attributes()`.
		/// Each bundle of attributes may be assigned to multiple
		/// objects.
		///
		/// Standard Attributes
		/// -------------------
		///
		/// "doubleSided", BoolData, true
		virtual AttributesInterfacePtr attributes( const IECore::CompoundObject *attributes ) = 0;

		IE_CORE_FORWARDDECLARE( ObjectInterface );

		/// A handle to an object in the renderer.
		class ObjectInterface : public IECore::RefCounted
		{

			public :

				IE_CORE_DECLAREMEMBERPTR( ObjectInterface )

				/// Assigns a transform to the object. For Interactive renders
				/// transforms may be modified at any time the renderer is paused.
				virtual void transform( const Imath::M44f &transform ) = 0;
				/// Assigns a block of attributes to the object, replacing any
				/// previously assigned attributes. For Interactive renders
				/// attributes may be modified at any time the renderer is paused.
				virtual void attributes( const AttributesInterface *attributes ) = 0;

			protected :

				virtual ~ObjectInterface();

		};

		/// Adds a named light to the render. The reference counting semantics of
		/// the returned Ptr are the same as for the object() method. A shader for
		/// the light is expected to be provided by a subsequently assigned attribute
		/// block in a renderer specific fashion. Object may be non-NULL to specify
		/// arbitrary geometry for a geometric area light, or NULL to indicate that
		/// the light shader specifies its own geometry internally (or is non-geometric
		/// in nature).
		virtual ObjectInterfacePtr light( const std::string &name, const IECore::Object *object = NULL ) = 0;

		/// Adds a named object to the render. The reference counting semantics of the
		/// returned Ptr are as follows :
		///
		/// - For Interactive renders, releasing the Ptr (removing the last reference)
		///   removes the object from the render.
		/// - For Batch and SceneDescription renders, releasing the Ptr flushes the
		///   object to the renderer.
		///
		/// \todo Rejig class hierarchy so we can have something less generic than
		/// Object here, but still pass Cameras and CoordinateSystems. Or should
		/// cameras and coordinate systems have their own dedicated calls? Perhaps they
		/// should, on the grounds that a streaming OpenGL render would need the camera
		/// first, and we can make that clearer if it has its own method?
		virtual ObjectInterfacePtr object( const std::string &name, const IECore::Object *object ) = 0;

		/// Performs the render - should be called after the
		/// entire scene has been specified using the methods
		/// above. Batch and SceneDescripton renders will have
		/// been completed upon return from this method. Interactive
		/// renders will return immediately and perform the
		/// rendering in the background, allowing pause() to be
		/// used to make edits before calling render() again.
		virtual void render() = 0;
		/// If an interactive render is running, pauses it so
		/// that edits may be made.
		virtual void pause() = 0;

	protected :

		Renderer();
		virtual ~Renderer();

		/// Construct a static instance of this to register a
		/// renderer implementation.
		/// \todo Derive this from RunTimeTyped::TypeDescription.
		template<class T>
		struct TypeDescription
		{

			/// \todo Take the type name from RunTimeTyped::staticTypeId().
			TypeDescription( const IECore::InternedString &typeName )
			{
				registerType( typeName, creator );
			}

			private :

				static Ptr creator( RenderType renderType, const std::string &fileName )
				{
					return new T( renderType, fileName );
				}

		};

	private :

		static void registerType( const IECore::InternedString &typeName, Ptr (*creator)( RenderType, const std::string & ) );


};

IE_CORE_DECLAREPTR( Renderer )

} // namespace IECoreScenePreview

#endif // IECORESCENEPREVIEW_RENDERER_H
