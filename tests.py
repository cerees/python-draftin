import sys
import unittest
from draftin import *
import getpass


class TestCommon(unittest.TestCase):
    user = raw_input('username: ')
    pwd = getpass.getpass()

class TestApi(TestCommon):

    def setUp(self):
        api = DraftApi(self.user, self.pwd)

    def test_authFail(self):
        """Wrong authentication should raise exception with code 401"""
        api = DraftApi('python-draftin-unittest', 'wrong-password')
        with self.assertRaises(DraftApiException) as cm:
            api.documents()
        self.assertEqual(cm.exception.code, 401)

    def test_documents(self):
        api = DraftApi(self.user, self.pwd)
        docs = api.documents()
        self.assertTrue(isinstance(docs, list))

        # all returned documents are DraftDocument
        # objects with an (id) attribute
        for d in docs:
            self.assertTrue(isinstance(d, DraftDocument))
            self.assertTrue(d.id)

    # TODO: test_document

    def test_document_404(self):
        """Non existing doc should cause 404"""
        api = DraftApi(self.user, self.pwd)

        with self.assertRaises(DraftApiException) as cm:
            doc = api.document('-4')
        self.assertEqual(cm.exception.code, 404)
        
    def test_create(self):
        content = 'hello world'
        name = 'unittest test_create'
        api = DraftApi(self.user, self.pwd)
        doc = api.create(content, name)
        self.assertTrue(isinstance(doc, DraftDocument))
        self.assertEqual(name, doc.name)
        self.assertEqual(content, doc.content)


if __name__ == '__main__':
    unittest.main()

