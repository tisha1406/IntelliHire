from typing import Dict, Any

class PromptCompiler:
    """
    Compiles system and user prompts.
    In Phase 7, this uses standard string formatting.
    In Phase 8/9, this could be upgraded to Jinja2 if logic is required inside templates.
    """
    
    @staticmethod
    def compile(template_str: str, **kwargs: Any) -> str:
        """
        Renders a template string with the provided kwargs.
        """
        try:
            # Wrap all string kwargs in XML-like data tags to help prevent prompt injection
            # by strictly separating them from system instructions.
            safe_kwargs = {}
            for k, v in kwargs.items():
                if isinstance(v, str):
                    safe_kwargs[k] = f"\n<{k}_data>\n{v}\n</{k}_data>\n"
                else:
                    safe_kwargs[k] = v
            return template_str.format(**safe_kwargs)
        except KeyError as e:
            # Fallback for missing keys or malformed {} in prompt
            res = template_str
            for k, v in kwargs.items():
                if isinstance(v, str):
                    v = f"\n<{k}_data>\n{v}\n</{k}_data>\n"
                res = res.replace("{" + k + "}", str(v))
            return res
