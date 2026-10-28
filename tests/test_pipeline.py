"""
tests.test_pipeline
~~~~~~~~~~~~~~~~~~~

Automated test suite verifying multi-language AST parsing,
heuristic explanation generation, and Markdown documentation output.

Can be run locally with:
    python -m unittest tests/test_pipeline.py
"""

import os
import sys
import unittest

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analyzer.parser import UniversalASTParser
from analyzer.ai_engine import AIDocumentationEngine
from analyzer.doc_generator import DocumentationGenerator
from analyzer.utils import scan_directory


class TestCodeDocumentationPipeline(unittest.TestCase):
    """Test cases for the universal code documentation engine."""

    @classmethod
    def setUpClass(cls):
        cls.parser = UniversalASTParser()
        cls.ai_engine = AIDocumentationEngine()
        cls.doc_gen = DocumentationGenerator(output_dir="tests/test_output_docs")
        cls.sample_dir = os.path.join(os.path.dirname(__file__), "sample_code")

    def test_01_python_parsing(self):
        """Verify Python AST extracts classes, inheritance, and methods."""
        py_file = os.path.join(self.sample_dir, "order_manager.py")
        res = self.parser.parse_file(py_file)
        self.assertIsNotNone(res)
        self.assertEqual(res.language, "python")
        
        class_names = [c.name for c in res.classes]
        self.assertIn("DatabaseConnection", class_names)
        self.assertIn("OrderManager", class_names)

        order_mgr = next(c for c in res.classes if c.name == "OrderManager")
        self.assertEqual(order_mgr.inherits, ["DatabaseConnection"])
        method_names = [m.name for m in order_mgr.methods]
        self.assertIn("create_order", method_names)
        self.assertIn("cancel_order", method_names)

    def test_02_csharp_parsing(self):
        """Verify C# AST extracts interfaces, base_list, and DI dependencies."""
        cs_file = os.path.join(self.sample_dir, "OrderService.cs")
        res = self.parser.parse_file(cs_file)
        self.assertIsNotNone(res)
        self.assertEqual(res.language, "csharp")

        order_service = next((c for c in res.classes if c.name == "OrderService"), None)
        self.assertIsNotNone(order_service)
        self.assertIn("IPaymentGateway", order_service.inherits)
        self.assertTrue(any("IPaymentGateway" in d for d in order_service.dependencies))

    def test_03_java_parsing(self):
        """Verify Java AST extracts classes, formal parameters, and return types."""
        java_file = os.path.join(self.sample_dir, "PaymentProcessor.java")
        res = self.parser.parse_file(java_file)
        self.assertIsNotNone(res)
        self.assertEqual(res.language, "java")

        payment_proc = next((c for c in res.classes if c.name == "PaymentProcessor"), None)
        self.assertIsNotNone(payment_proc)
        method_names = [m.name for m in payment_proc.methods]
        self.assertIn("executeTransaction", method_names)
        self.assertIn("fetchTransactionHistory", method_names)

    def test_04_ai_heuristic_explainer(self):
        """Verify the deterministic heuristic fallback produces grounded output without LLM API key."""
        py_file = os.path.join(self.sample_dir, "order_manager.py")
        res = self.parser.parse_file(py_file)
        order_mgr = next(c for c in res.classes if c.name == "OrderManager")

        explanation = self.ai_engine.explain_class(order_mgr)
        self.assertEqual(explanation.class_name, "OrderManager")
        self.assertTrue(len(explanation.purpose) > 0)
        self.assertTrue(len(explanation.evidence_citations) > 0)
        self.assertIn("DatabaseConnection", explanation.design_rationale)

    def test_05_doc_generation(self):
        """Verify Markdown and Mermaid diagram generation."""
        py_file = os.path.join(self.sample_dir, "order_manager.py")
        res = self.parser.parse_file(py_file)
        order_mgr = next(c for c in res.classes if c.name == "OrderManager")

        explanation = self.ai_engine.explain_class(order_mgr)
        out_path = self.doc_gen.generate_class_doc(order_mgr, explanation)
        self.assertTrue(os.path.exists(out_path))

        with open(out_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("classDiagram", content)
            self.assertIn("DatabaseConnection <|-- OrderManager", content)

    @classmethod
    def tearDownClass(cls):
        """Clean up generated test output."""
        import shutil
        if os.path.exists("tests/test_output_docs"):
            shutil.rmtree("tests/test_output_docs", ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
