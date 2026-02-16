from django.test import TestCase

from apps.docs.models import Document, Tag


class TagModelTests(TestCase):
    def test_str(self):
        t = Tag.objects.create(name="python")
        self.assertEqual(str(t), "python")


class DocumentModelTests(TestCase):
    def test_build_slug_normalizes_and_truncates(self):
        slug = Document.build_slug("Olá Mundo -- Django!!")
        self.assertTrue(slug)
        self.assertLessEqual(len(slug), 220)

    def test_build_slug_empty_falls_back_to_doc(self):
        self.assertEqual(Document.build_slug(""), "doc")
        self.assertEqual(Document.build_slug("   "), "doc")
