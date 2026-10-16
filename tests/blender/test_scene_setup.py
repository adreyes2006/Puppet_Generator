import unittest

import bpy

from puppet_pipeline.common import naming
from puppet_pipeline.common.scene import reset_puppet_scene


class SceneSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.unrelated_collection = bpy.data.collections.new("UNRELATED")
        bpy.context.scene.collection.children.link(self.unrelated_collection)
        unrelated_mesh = bpy.data.meshes.new("unrelated.data")
        self.unrelated_object = bpy.data.objects.new("unrelated", unrelated_mesh)
        self.unrelated_collection.objects.link(self.unrelated_object)

    def tearDown(self) -> None:
        reset_puppet_scene()
        if self.unrelated_object.name in bpy.data.objects:
            bpy.data.objects.remove(self.unrelated_object, do_unlink=True)
        if self.unrelated_collection.name in bpy.data.collections:
            bpy.data.collections.remove(self.unrelated_collection)

    def test_setup_creates_exact_nested_collection_hierarchy(self) -> None:
        collections = reset_puppet_scene()

        self.assertEqual(collections.root.name, naming.ROOT_COLLECTION_NAME)
        self.assertEqual(collections.geometry.name, naming.GEOMETRY_COLLECTION_NAME)
        self.assertEqual(collections.rig.name, naming.RIG_COLLECTION_NAME)
        self.assertIn(collections.root, bpy.context.scene.collection.children.values())
        self.assertIn(collections.geometry, collections.root.children.values())
        self.assertIn(collections.rig, collections.root.children.values())

    def test_setup_removes_prior_generated_objects_and_data(self) -> None:
        collections = reset_puppet_scene()
        stale_mesh = bpy.data.meshes.new("pup.stale.data")
        stale_object = bpy.data.objects.new("pup.stale", stale_mesh)
        collections.geometry.objects.link(stale_object)
        stale_armature = bpy.data.armatures.new(naming.ARMATURE_DATA_NAME)
        stale_rig = bpy.data.objects.new(naming.ARMATURE_OBJECT_NAME, stale_armature)
        collections.rig.objects.link(stale_rig)

        reset_puppet_scene()

        self.assertNotIn("pup.stale", bpy.data.objects)
        self.assertNotIn("pup.stale.data", bpy.data.meshes)
        self.assertNotIn(naming.ARMATURE_OBJECT_NAME, bpy.data.objects)
        self.assertNotIn(naming.ARMATURE_DATA_NAME, bpy.data.armatures)

    def test_setup_preserves_unrelated_scene_data(self) -> None:
        reset_puppet_scene()
        reset_puppet_scene()

        self.assertIn(self.unrelated_collection.name, bpy.data.collections)
        self.assertIn(self.unrelated_object.name, bpy.data.objects)
        self.assertIs(
            bpy.data.objects[self.unrelated_object.name],
            self.unrelated_object,
        )

    def test_repeated_setup_is_idempotent(self) -> None:
        first = reset_puppet_scene()
        first_names = (first.root.name, first.geometry.name, first.rig.name)
        second = reset_puppet_scene()

        self.assertEqual(
            first_names,
            (second.root.name, second.geometry.name, second.rig.name),
        )
        self.assertEqual(
            sum(
                collection.name == naming.ROOT_COLLECTION_NAME
                for collection in bpy.data.collections
            ),
            1,
        )
        self.assertFalse(
            any(
                collection.name.startswith(f"{naming.ROOT_COLLECTION_NAME}.")
                and collection.name[-3:].isdigit()
                for collection in bpy.data.collections
            )
        )


if __name__ == "__main__":
    unittest.main()
