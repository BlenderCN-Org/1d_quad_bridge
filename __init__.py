bl_info = {
    'name': 'Quad Bridge',
    'category': 'Mesh',
    'author': 'Nikita Akimov',
    'version': (0, 2, 1),
    'blender': (2, 79, 0),
    'location': 'The 3D_View window - T-panel - the 1D tab',
    'wiki_url': 'https://github.com/Korchy/1d_quad_bridge',
    'tracker_url': 'https://github.com/Korchy/1d_quad_bridge',
    'description': 'Quad Bridge'
}
 
from . import quadbridge


def register():
    quadbridge.register()
 
 
def unregister():
    quadbridge.unregister()
 
 
if __name__ == "__main__":
    register()