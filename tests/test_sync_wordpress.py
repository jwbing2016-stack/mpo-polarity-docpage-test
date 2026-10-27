import importlib.util
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sync", ROOT/"scripts/sync_wordpress.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

class SyncTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT/"wordpress-sync.json").read_text())
        self.site, self.items = sync.prepare(self.config)
        self.article, self.payload = self.items[0]
    def response(self, payload=None):
        return {"ID":4,"site_ID":258218432,"URL":self.article["url"],
                "status":"publish","content":(payload or self.payload)["content"]}
    def test_original_article_survives_conversion(self):
        content = self.payload["content"]
        self.assertEqual(content.count("<table>"), 2)
        self.assertEqual(content.count("<!-- wp:heading"), 24)
        self.assertIn('href="https://cablefam.com/"', content)
    def test_unknown_block_is_rejected(self):
        with self.assertRaises(RuntimeError):
            sync.blocks("<blockquote><p>unhandled</p></blockquote>")
    def test_update_same_id_and_read_back(self):
        def fake(site, post, token, payload=None):
            self.assertEqual((site,post,token),(258218432,4,"test-only"))
            return self.response(payload)
        with patch.dict(os.environ,{"WORDPRESS_ACCESS_TOKEN":"test-only"}):
            with patch.object(sync,"request",side_effect=fake) as req:
                sync.run()
                self.assertEqual(req.call_count,3)
                self.assertEqual(req.call_args_list[1].args[1],4)
    def test_wrong_target_prevents_write(self):
        wrong = self.response()
        wrong["ID"] = 99
        with patch.dict(os.environ,{"WORDPRESS_ACCESS_TOKEN":"test-only"}):
            with patch.object(sync,"request",return_value=wrong) as req:
                with self.assertRaises(RuntimeError):
                    sync.run()
                self.assertEqual(req.call_count,1)
    def test_sanitized_link_is_detected(self):
        bad = self.response()
        bad["content"] = bad["content"].replace('href="https://cablefam.com/"','href="https://invalid.example/"')
        with patch.dict(os.environ,{"WORDPRESS_ACCESS_TOKEN":"test-only"}):
            with patch.object(sync,"request",side_effect=[self.response(),self.response(),bad]):
                with self.assertRaises(RuntimeError):
                    sync.run()
    def test_no_token_performs_no_request(self):
        with patch.dict(os.environ,{"WORDPRESS_ACCESS_TOKEN":""}):
            with patch.object(sync,"request") as req:
                with self.assertRaises(RuntimeError):
                    sync.run()
                req.assert_not_called()
    def test_missing_mapping_is_not_creation(self):
        self.config["articles"][0]["post_id"] = 0
        with self.assertRaises(RuntimeError):
            sync.prepare(self.config)

if __name__ == "__main__":
    unittest.main()
