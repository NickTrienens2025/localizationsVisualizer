import re
from typing import List, Dict, Any, Optional
from datetime import datetime


class EnumExporter:
    def __init__(self, graph_service):
        self.graph_service = graph_service
    
    def to_upper_camel_case(self, text: str) -> str:
        """Convert text to UpperCamelCase"""
        if not text:
            return "Unknown"
        
        # Clean the text
        text = re.sub(r'[^a-zA-Z0-9\s]', ' ', text)
        words = text.split()
        return ''.join(word.capitalize() for word in words if word)
    
    def to_camel_case_key(self, text: str) -> str:
        """Convert text to camelCase for enum cases"""
        if not text:
            return "unknown"
        
        # Remove special characters
        text = re.sub(r'[^a-zA-Z0-9\s\-_.]', '', text)
        
        # Insert separators at camelCase boundaries
        # 1. Lowercase to uppercase transitions
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', '_', text)
        # 2. Multiple consecutive uppercase letters followed by lowercase (e.g., "NHLLeaders" -> "NHL_Leaders")
        text = re.sub(r'(?<=[A-Z])(?=[A-Z][a-z])', '_', text)
        
        # Split by common separators including our inserted underscores
        parts = re.split(r'[\s\-_.]+', text)
        
        if not parts:
            return "unknown"
        
        # First part lowercase, rest capitalized
        result = parts[0].lower()
        for part in parts[1:]:
            if part:
                result += part.capitalize()
        
        return result
    
    def generate_case_name(self, key: str) -> str:
        """Generate a valid Swift case name from the entry key"""
        # Remove section prefix if present
        clean_key = key.split('.')[-1] if '.' in key else key
        
        case_name = self.to_camel_case_key(clean_key)
        
        # Ensure it's a valid Swift identifier
        if case_name and case_name[0].isdigit():
            case_name = "key" + case_name
        
        # Escape Swift keywords
        swift_keywords = {
            "case", "class", "struct", "enum", "protocol", "let", "var", "func", 
            "in", "for", "while", "if", "else", "return", "public", "private", 
            "internal", "static", "default", "switch"
        }
        
        if case_name in swift_keywords:
            return f"`{case_name}`"
        
        return case_name or "unknown"
    
    def extract_substitution_parameters(self, value: str) -> str:
        """Extract substitution parameters from a localized string in order of appearance"""
        if not value:
            return ""
        
        parameters = []
        i = 0
        
        # Scan the string from left to right to preserve order
        while i < len(value):
            if value[i] == '%' and i + 1 < len(value):
                next_char = value[i + 1]
                if next_char == '@':
                    parameters.append('String')
                    i += 2  # Skip both % and @
                elif next_char == 'd':
                    parameters.append('Int')
                    i += 2  # Skip both % and d
                else:
                    i += 1
            else:
                i += 1
        
        return ', '.join(parameters)
    
    async def generate_swift_enum(self) -> str:
        """Generate Swift enum code from Contentful data"""
        # Get all localization entries and group by section
        all_entries = await self.graph_service.get_all_localization_entries()
        sections = await self.graph_service.get_sections()
        
        # Group entries by section
        entries_by_section = {}
        for entry in all_entries:
            section_name = entry.get('section', '')
            if section_name:
                if section_name not in entries_by_section:
                    entries_by_section[section_name] = []
                entries_by_section[section_name].append(entry)
        
        timestamp = datetime.now().isoformat()
        
        swift_code = f"""import Foundation
import LocalizationLibrary 
// Generated Swift Enums from Contentful Database
// Generated on: {timestamp}
// Total entries: {len(all_entries)}

public enum Localizations {{

"""
        
        # Sort sections by title
        sorted_sections = sorted(sections, key=lambda x: x.get('title', ''))
        
        for section in sorted_sections:
            section_key = section.get('key', '')
            section_entries = entries_by_section.get(section_key, [])
            swift_code += await self.generate_section_enum_from_entries(section, section_entries, level=1)
        
        swift_code += "}\n"
        
        return swift_code

    async def generate_swift_testing_helper(self) -> str:
        """Generate Swift testing helper file with 300 consistent test cases"""
        # Get all localization entries and group by section
        all_entries = await self.graph_service.get_all_localization_entries()
        sections = await self.graph_service.get_sections()
        
        # Group entries by section
        entries_by_section = {}
        for entry in all_entries:
            section_name = entry.get('section', '')
            if section_name:
                if section_name not in entries_by_section:
                    entries_by_section[section_name] = []
                entries_by_section[section_name].append(entry)
        
        # Collect all test cases
        all_test_cases = []
        sorted_sections = sorted(sections, key=lambda x: x.get('title', ''))
        
        for section in sorted_sections:
            section_key = section.get('key', '')
            section_entries = entries_by_section.get(section_key, [])
            _, section_test_cases = await self.generate_section_enum_from_entries_with_test_cases(section, section_entries, level=1)
            all_test_cases.extend(section_test_cases)
        
        timestamp = datetime.now().isoformat()
        
        testing_code = f"""import Foundation
import LocalizationLibrary
// Generated Swift Testing Helper from Contentful Database
// Generated on: {timestamp}
// Total test cases: {len(all_test_cases)}

#if DEBUG
extension Localizations {{
    
{self.generate_consistent_testing_helper(all_test_cases, level=1)}
}}
#endif
"""
        
        return testing_code

    def generate_consistent_testing_helper(self, all_test_cases: List[Dict], level: int) -> str:
        """Generate testing helper with 300 consistent test cases"""
        indent = "    " * level
        
        # Group test cases by section for better distribution
        cases_by_section = {}
        for test_case in all_test_cases:
            section_name = test_case['section_name']
            if section_name not in cases_by_section:
                cases_by_section[section_name] = []
            cases_by_section[section_name].append(test_case)
        
        sections = list(cases_by_section.keys())
        if not sections:
            return ""
        
        # Generate 300 consistent test cases with good section distribution
        consistent_cases = []
        target_count = 300
        
        # Use deterministic but distributed approach
        for i in range(target_count):
            # Switch sections frequently using deterministic pattern
            section_index = (i * 7 + i // 3) % len(sections)  # Mix sections more frequently
            current_section = sections[section_index]
            section_cases = cases_by_section[current_section]
            
            # Pick case from current section using deterministic pattern
            case_index = (i * 3 + i // 5) % len(section_cases)
            test_case = section_cases[case_index]
            
            section_name = test_case['section_name']
            case_name = test_case['case_name']
            parameters = test_case['parameters']
            
            if parameters:
                # Generate consistent parameters based on index
                param_types = parameters.split(', ')
                sample_params = []
                for j, param_type in enumerate(param_types):
                    if 'String' in param_type:
                        sample_params.append(f'"Test{i+1}Param{j+1}"')
                    elif 'Int' in param_type:
                        sample_params.append(str((i + 1) * (j + 1)))
                    else:
                        sample_params.append(f'"Value{i+1}_{j+1}"')
                
                params_str = ', '.join(sample_params)
                consistent_cases.append(f'{section_name}.{case_name}({params_str})')
            else:
                consistent_cases.append(f'{section_name}.{case_name}')
        
        # Format the cases with proper indentation
        formatted_cases = []
        for case in consistent_cases:
            formatted_cases.append(f'{indent}        {case}')
        
        cases_text = ',\n'.join(formatted_cases)
        
        helper_code = f"""{indent}// MARK: - Testing Helper (300 Consistent Cases)
{indent}public static let testCases: [any LocalizationKey] = [
{cases_text}
{indent}    ]
{indent}
{indent}public static func generateRandomTestCases(count: Int = 10) -> [any LocalizationKey] {{
{indent}    return Array(testCases.shuffled().prefix(count))
{indent}}}
{indent}
{indent}public static func generateConsistentTestCases(count: Int = 10) -> [any LocalizationKey] {{
{indent}    return Array(testCases.prefix(count))
{indent}}}
{indent}
{indent}public static func getAllTestCases() -> [any LocalizationKey] {{
{indent}    return testCases
{indent}}}"""
        
        return helper_code

    async def generate_section_enum_from_entries_with_test_cases(self, section: Dict, entries: List[Dict], level: int) -> tuple[str, List[Dict]]:
        """Generate enum for a section from localization entries"""
        indent = "    " * level
        section_name = self.to_upper_camel_case(section.get('title', 'Unknown'))
        section_key = section.get('key', '')
        
        enum_code = f'{indent}public enum {section_name}: LocalizationKey {{\n'
        enum_code += f'{indent}    public var filename: String {{ "{section_key}" }}\n\n'
        
        case_definitions = []
        key_mappings = []
        
        # Generate cases for entries
        sorted_entries = sorted(entries, key=lambda x: x.get('key', ''))
        for entry in sorted_entries:
            key = entry.get('key', '')
            value = entry.get('value', '')
            
            if key:
                case_name = self.generate_case_name(key)
                parameters = self.extract_substitution_parameters(value)
                
                if parameters:
                    case_definitions.append(f"{indent}    case {case_name}({parameters})")
                else:
                    case_definitions.append(f"{indent}    case {case_name}")
                
                key_mappings.append((case_name, key, parameters))
        
        if case_definitions:
            enum_code += '\n'.join(case_definitions)
            
            # Generate computed property for key
            enum_code += f"\n\n{indent}    public var key: String {{\n"
            enum_code += f"{indent}        switch self {{\n"
            
            for case_name, entry_key, parameters in key_mappings:
                if parameters:
                    param_count = len(parameters.split(','))
                    case_pattern = ', '.join(['_'] * param_count)
                    enum_code += f'{indent}        case .{case_name}({case_pattern}): return "{entry_key}"\n'
                else:
                    enum_code += f'{indent}        case .{case_name}: return "{entry_key}"\n'
            
            enum_code += f"{indent}        }}\n"
            enum_code += f"{indent}    }}\n"
            
            # Generate computed property for hasParameters
            enum_code += f"\n{indent}    public var hasParameters: Bool {{\n"
            
            # Collect cases with parameters
            cases_with_parameters = [case_name for case_name, _, parameters in key_mappings if parameters]
            
            if cases_with_parameters:
                enum_code += f"{indent}        switch self {{\n"
                cases_list = ', '.join([f'.{case_name}' for case_name in cases_with_parameters])
                enum_code += f"{indent}        case {cases_list}:\n"
                enum_code += f"{indent}            return true\n"
                enum_code += f"{indent}        default:\n"
                enum_code += f"{indent}            return false\n"
                enum_code += f"{indent}        }}\n"
            else:
                enum_code += f"{indent}        return false\n"
            
            enum_code += f"{indent}    }}\n"
            
            # Generate computed property for parameters
            enum_code += f"\n{indent}    public var parameters: [any CVarArg]? {{\n"
            
            # Collect cases with parameters
            cases_with_parameters = [(case_name, parameters) for case_name, _, parameters in key_mappings if parameters]
            
            if cases_with_parameters:
                enum_code += f"{indent}        switch self {{\n"
                
                for case_name, parameters in cases_with_parameters:
                    param_count = len(parameters.split(','))
                    param_names = ', '.join([f'param{i+1}' for i in range(param_count)])
                    enum_code += f'{indent}        case let .{case_name}({param_names}):\n'
                    param_array = ', '.join([f'param{i+1}' for i in range(param_count)])
                    enum_code += f'{indent}            return [{param_array}]\n'
                
                enum_code += f"{indent}        default:\n"
                enum_code += f"{indent}            return nil\n"
                enum_code += f"{indent}        }}\n"
            else:
                enum_code += f"{indent}        return nil\n"
            
            enum_code += f"{indent}    }}\n"
        
        enum_code += f"{indent}}}\n\n"
        print(f"DEBUG: Generated enum for section '{section_name}' with {len(entries)} entries")
        
        # Prepare test case data
        test_cases = []
        for case_name, entry_key, parameters in key_mappings:
            test_cases.append({
                'section_name': section_name,
                'case_name': case_name,
                'parameters': parameters
            })
        
        return enum_code, test_cases

    async def generate_section_enum_from_entries(self, section: Dict, entries: List[Dict], level: int) -> str:
        """Generate enum for a section from localization entries (backward compatibility)"""
        enum_code, _ = await self.generate_section_enum_from_entries_with_test_cases(section, entries, level)
        return enum_code

 

    async def generate_python_migration_script(self) -> str:
        """Generate Python migration script to find and replace old localization patterns"""
        from jinja2 import Template
        import os
        
        # Get all localization entries to build a mapping
        all_entries = await self.graph_service.get_all_localization_entries()
        sections = await self.graph_service.get_sections()
        
        # Build mapping from original keys to new enum paths
        key_to_enum_mapping = {}
        entries_by_section = {}
        
        for entry in all_entries:
            section_name = entry.get('section', '')
            if section_name:
                if section_name not in entries_by_section:
                    entries_by_section[section_name] = []
                entries_by_section[section_name].append(entry)
        
        # Create mapping from original keys to enum paths
        for section in sections:
            section_key = section.get('key', '')
            section_title = section.get('title', 'Unknown')
            section_enum_name = self.to_upper_camel_case(section_title)
            section_entries = entries_by_section.get(section_key, [])
            
            for entry in section_entries:
                original_key = entry.get('originalKey', '')
                if original_key:
                    case_name = self.generate_case_name(original_key)
                    value = entry.get('value', '')
                    parameters = self.extract_substitution_parameters(value)
                    
                    if parameters:
                        # Has parameters - need to specify parameter placeholders
                        param_types = parameters.split(', ')
                        param_placeholders = []
                        for i, param_type in enumerate(param_types):
                            if 'String' in param_type:
                                param_placeholders.append('"<string_param>"')
                            elif 'Int' in param_type:
                                param_placeholders.append('<int_param>')
                        param_str = ', '.join(param_placeholders)
                        enum_path = f"Localizations.{section_enum_name}.{case_name}({param_str})"
                    else:
                        enum_path = f"Localizations.{section_enum_name}.{case_name}"
                    
                    key_to_enum_mapping[original_key] = {
                        'enum_path': enum_path,
                        'has_parameters': bool(parameters),
                        'parameters': parameters
                    }
        
        timestamp = datetime.now().isoformat()
        
        # Read the template file
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'python_migration_script.py.j2')
        with open(template_path, 'r', encoding='utf-8') as f:
            template_content = f.read()
        
        # Create template and render
        template = Template(template_content)
        script_content = template.render(
            timestamp=timestamp,
            key_mapping=key_to_enum_mapping
        )
        
        return script_content
