import unittest
from datetime import datetime
from template_parser import TemplateParser

class TestTemplateParser(unittest.TestCase):
    def setUp(self):
        self.simple_template = "Hello {{ name }}!"
        self.condition_template = """
        {% if show %}
        Show this content
        {% else %}
        Don't show this
        {% endif %}
        """
        self.loop_template = """
        {% for item in items %}
        - {{ item }}
        {% endfor %}
        """
        self.custom_func_template = "{{= greet(name) }}"
        self.nested_template = """
        {% if user.is_admin %}
        Welcome admin {{ user.name }}!
        {% else %}
        Welcome user {{ user.name }}!
        {% endif %}
        """
        
    def test_simple_variable(self):
        parser = TemplateParser(self.simple_template)
        result = parser.render({"name": "World"})
        self.assertEqual(result.strip(), "Hello World!")
        
    def test_condition_true(self):
        parser = TemplateParser(self.condition_template)
        result = parser.render({"show": True})
        self.assertIn("Show this content", result)
        self.assertNotIn("Don't show this", result)
        
    def test_condition_false(self):
        parser = TemplateParser(self.condition_template)
        result = parser.render({"show": False})
        self.assertIn("Don't show this", result)
        self.assertNotIn("Show this content", result)
        
    def test_loop(self):
        parser = TemplateParser(self.loop_template)
        result = parser.render({"items": ["one", "two", "three"]})
        self.assertIn("- one", result)
        self.assertIn("- two", result)
        self.assertIn("- three", result)
        
    def test_empty_loop(self):
        parser = TemplateParser(self.loop_template)
        result = parser.render({"items": []})
        self.assertEqual(result.strip(), "")
        
    def test_custom_function(self):
        def greet(name):
            return f"Hello, {name}!"
            
        parser = TemplateParser(self.custom_func_template)
        parser.register_function("greet", greet)
        result = parser.render({"name": "World"})
        self.assertEqual(result.strip(), "Hello, World!")
        
    def test_nested_attributes(self):
        parser = TemplateParser(self.nested_template)
        result = parser.render({
            "user": {
                "name": "Alice",
                "is_admin": True
            }
        })
        self.assertIn("Welcome admin Alice!", result)
        
    def test_error_handling(self):
        error_template = "{{ undefined_var }}"
        parser = TemplateParser(error_template)
        result = parser.render({})
        self.assertIn("", result)  # Should handle missing var gracefully
        
    def test_eval_security(self):
        malicious_template = "{{= __import__('os').system('rm -rf /') }}"
        parser = TemplateParser(malicious_template)
        with self.assertRaises(Exception):
            parser.render({})
            
    def test_multi_line_condition(self):
        multi_line_template = """
        {% if 
            # Multi-line condition
            x = 10
            y = 20
            __result__ = x < y
        %}
        Condition passed
        {% endif %}
        """
        parser = TemplateParser(multi_line_template)
        result = parser.render({})
        self.assertIn("Condition passed", result)

if __name__ == '__main__':
    unittest.main()