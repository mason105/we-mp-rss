import re
from typing import Any, Dict, List, Union
# """
# 模板引擎使用示例

# 基础用法:
# 1. 简单变量替换: {{variable}}
# 2. 条件判断: {% if condition %}...{% endif %}
# 3. 循环结构: {% for item in items %}...{% endfor %}
# """
class TemplateParser:
    """A lightweight template engine supporting variables, conditions and loops."""
    
    def __init__(self, template: str):
        """Initialize the template parser with a template string."""
        self.template = template
        self.compiled = None
        
    def compile_template(self) -> None:
        """Compile the template into an intermediate representation."""
        # Split template into static parts and control blocks
        pattern = re.compile(
            r'(\{\%.*?\%\})|'  # control blocks {% ... %}
            r'(\{\{.*?\}\})'    # variables {{ ... }}
        )
        self.compiled = pattern.split(self.template)
        
    def render(self, context: Dict[str, Any]) -> str:
        """
        Render the template with the given context.
        
        Args:
            context: A dictionary containing variables for template rendering
            
        Returns:
            The rendered template as a string
        """
        if self.compiled is None:
            self.compile_template()
            
        output = []
        i = 0
        while i < len(self.compiled):
            part = self.compiled[i]
            
            if part is None:
                i += 1
                continue
                
            # Handle variables {{ var }} and nested {{ var.attr }}
            if part.startswith('{{') and part.endswith('}}'):
                var_expr = part[2:-2].strip()
                if '.' in var_expr:
                    # Handle nested attribute access
                    parts = var_expr.split('.')
                    current = context.get(parts[0], {})
                    for part_name in parts[1:]:
                        if isinstance(current, dict):
                            current = current.get(part_name, '')
                        else:
                            current = getattr(current, part_name, '')
                        if current is None:
                            current = ''
                            break
                    output.append(str(current))
                else:
                    # Simple variable access
                    output.append(str(context.get(var_expr, '')))
                i += 1
                
            # Handle control blocks {% ... %}
            elif part.startswith('{%') and part.endswith('%}'):
                block = part[2:-2].strip()
                
                # Handle if condition
                if block.startswith('if '):
                    condition = block[3:].strip()
                    result = bool(self._evaluate_condition(condition, context))
                    # print(f"DEBUG - Evaluating condition '{condition}': result={result}")
                    
                    # Find matching endif using helper method
                    endif_idx = self._skip_control_block(i, 'if', 'endif')
                    if endif_idx == len(self.compiled):
                        # print("DEBUG - Error: No matching endif found for if block")
                        i += 1
                        continue
                    
                    # Find else if exists
                    else_idx = -1
                    for j in range(i+1, endif_idx):
                        part = self.compiled[j]
                        if isinstance(part, str) and part.strip() in ('{% else %}', 'else'):
                            else_idx = j
                            break
                    
                    # print(f"DEBUG - Control block boundaries: else={else_idx}, endif={endif_idx}")
                    
                    # Process the appropriate block
                    if result:
                        # Process if block (from current position to else or endif)
                        end_idx = else_idx if else_idx != -1 else endif_idx
                        if_content = self.compiled[i+1:end_idx]
                        # print(f"DEBUG - Processing if block from {i+1} to {end_idx}")
                        
                        if_parser = TemplateParser('')
                        if_parser.compiled = if_content
                        rendered = if_parser.render(context)
                        output.append(rendered)
                    elif else_idx != -1:
                        # Process else block
                        else_content = self.compiled[else_idx+1:endif_idx]
                        # print(f"DEBUG - Processing else block from {else_idx+1} to {endif_idx}")
                        
                        else_parser = TemplateParser('')
                        else_parser.compiled = else_content
                        rendered = else_parser.render(context)
                        output.append(rendered)
                    
                    # Skip to after endif
                    i = endif_idx + 1
                    
                # Handle for loop
                elif block.startswith('for ') and ' in ' in block:
                    loop_var, iterable = self._parse_for_block(block)
                    items = self._get_iterable(iterable, context)
                    
                    # Collect loop content
                    loop_content = []
                    j = i + 1
                    while j < len(self.compiled):
                        inner_part = self.compiled[j]
                        if (isinstance(inner_part, str) and 
                            inner_part.startswith('{% endfor %}')):
                            break
                        loop_content.append(str(inner_part) if inner_part else '')
                        j += 1
                        
                    # Render loop
                    # print(f"DEBUG - For loop items: {items}")  # Debug
                    loop_output = []
                    for item_idx, item in enumerate(items):
                        loop_context = context.copy()
                        loop_context[loop_var] = item
                        # print(f"DEBUG - Processing item {item_idx}: {item}")  # Debug
                        
                        # Render loop content with current item
                        item_output = []
                        for part in loop_content:
                            if part is None:
                                continue
                                
                            # print(f"DEBUG - Processing part: {repr(part)}")  # Debug
                            
                            if isinstance(part, str) and part.startswith('{{') and part.endswith('}}'):
                                # Handle variable reference
                                var_expr = part[2:-2].strip()
                                # print(f"DEBUG - Evaluating variable: {var_expr}")  # Debug
                                
                                if '.' in var_expr:
                                    # Handle nested attributes
                                    parts = var_expr.split('.')
                                    current = loop_context.get(parts[0], {})
                                    for part_name in parts[1:]:
                                        if isinstance(current, dict):
                                            current = current.get(part_name, '')
                                        else:
                                            current = getattr(current, part_name, '')
                                        if current is None:
                                            current = ''
                                            break
                                    value = str(current)
                                else:
                                    # Handle simple variable
                                    value = str(loop_context.get(var_expr, ''))
                                
                                # print(f"DEBUG - Variable value: {value}")  # Debug
                                item_output.append(value)
                            else:
                                # Handle literal text (preserve whitespace and newlines)
                                item_output.append(str(part))
                        
                        rendered_item = ''.join(item_output)
                        # print(f"DEBUG - Rendered item {item_idx}:\n{repr(rendered_item)}")  # Debug
                        loop_output.append(rendered_item)
                    
                    if loop_output:
                        # Join all loop items with newlines and add to output
                        loop_result = '\n'.join(loop_output)
                        output.append(loop_result)
                    else:
                        # print("DEBUG - No loop output generated")
                        pass
                    
                    # Skip to end of loop
                    i = j + 1
                    
                # Handle endif/endfor
                elif block in ('endif', 'endfor'):
                    i += 1
                    
                else:
                    i += 1
                    
            # Static text
            else:
                output.append(str(part) if part else '')
                i += 1
                
        # Clean up the output by removing excessive newlines
        result = ''.join(output)
        return self._clean_output(result)
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression in the given context."""
        try:
            # Handle nested attribute access (e.g. user.is_admin)
            if '.' in condition:
                parts = condition.split('.')
                current = context.get(parts[0], {})
                for part in parts[1:]:
                    if isinstance(current, dict):
                        current = current.get(part, None)
                    else:
                        current = getattr(current, part, None)
                    if current is None:
                        return False
                # Handle empty collections
                if isinstance(current, (list, dict, set)) and not current:
                    return False
                return bool(current)
            
            # Handle direct variable reference
            if condition in context:
                value = context[condition]
                # print(f"DEBUG - Evaluating condition '{condition}': type={type(value)}, value={value}")  # Debug
                if isinstance(value, (list, dict, set)):
                    return len(value) > 0  # 所有集合类型统一检查长度
                return bool(value)  # 其他类型保持现有逻辑
                
            # Evaluate complex expressions
            return bool(eval(condition, {}, context))
        except:
            return False
            
    def _skip_control_block(self, start_idx: int, start_tag: str, end_tag: str) -> int:
        """Skip a control block until matching end tag is found."""
        if start_idx >= len(self.compiled):
            return len(self.compiled)
            
        depth = 1
        i = start_idx + 1
        # print(f"DEBUG - Searching for {end_tag} starting from {start_idx}")
        
        while i < len(self.compiled):
            part = self.compiled[i]
            if isinstance(part, str) and part.startswith('{%') and part.endswith('%}'):
                block = part[2:-2].strip()
                # print(f"DEBUG - Token {i}: {block} (depth={depth})")
                
                # Handle nested blocks
                if block.startswith('if ') or block.startswith('for '):
                    depth += 1
                    # print(f"DEBUG - Found nested block, depth increased to {depth}")
                elif block == end_tag:
                    depth -= 1
                    # print(f"DEBUG - Found {end_tag}, depth decreased to {depth}")
                    if depth == 0:
                        # print(f"DEBUG - Found matching {end_tag} at {i}")
                        return i
                elif block == 'else' and depth == 1:
                    # print(f"DEBUG - Found else at {i}")
                    # Don't decrease depth for else blocks
                    pass
                elif block in ['endif', 'endfor'] and depth > 1:
                    depth -= 1
                    # print(f"DEBUG - Found closing tag in nested block, depth decreased to {depth}")
            
            i += 1
        
        # print(f"DEBUG - Error: Reached end without finding matching {end_tag} (current depth: {depth})")
        # print(f"DEBUG - Last processed block: {self.compiled[i-1] if i > 0 else 'None'}")
        return len(self.compiled)

    def _clean_output(self, output: str) -> str:
        """Clean up the final output by removing excessive newlines and whitespace."""
        lines = output.split('\n')
        cleaned = []
        prev_line_empty = False
        
        for line in lines:
            stripped = line.strip()
            
            # Skip empty lines between list items
            if not stripped and cleaned and cleaned[-1].strip().startswith('-'):
                continue
                
            # Skip consecutive empty lines
            if not stripped and prev_line_empty:
                continue
                
            cleaned.append(line)
            prev_line_empty = not stripped
            
        # Ensure exactly one newline at end
        return '\n'.join(cleaned).strip() + '\n'
        
    def _parse_for_block(self, block: str) -> tuple:
        """Parse a for block into loop variable and iterable parts."""
        parts = block[4:].split(' in ', 1)
        return parts[0].strip(), parts[1].strip()
        
    def _get_iterable(self, iterable: str, context: Dict[str, Any]) -> List[Any]:
        """Get an iterable from context or evaluate expression."""
        if iterable in context:
            return context[iterable]
        try:
            return eval(iterable, {}, context)
        except:
            return []
            
    def _render_parts(self, parts: List[Union[str, None]], context: Dict[str, Any]) -> str:
        """Render a list of template parts with the given context."""
        temp_parser = TemplateParser('')
        temp_parser.compiled = parts
        return temp_parser.render(context)


# Example usage
if __name__ == '__main__':
    template = """
    <html>
    <body>
        <h1>Hello {{ name }}!</h1>
        
        {% if show_details %}
        <div class="details">
            <p>Your details:</p>
            <ul>
                {% for item in items %}
                <li>{{ item }}</li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </body>
    </html>
    """
    
    context = {
        'name': 'World',
        'show_details': True,
        'items': ['Item 1', 'Item 2', 'Item 3']
    }
    
    parser = TemplateParser(template)
    result = parser.render(context)
    print(result)