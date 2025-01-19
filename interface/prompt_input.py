from .display import trunc

class InputHandler:
    """Enhanced input handling"""
    
    def prompt_yn(self, question: str, default: str | None = None) -> bool:
        """Yes/No prompt with optional default."""
        choices = ("", "y", "n") if default in ("yes", "no") else ("y", "n")
        hint = "Y/n" if default == "yes" else "y/n"
        hint = "y/N" if default == "no" else hint
        reply = None
        while reply not in choices:
            reply = input(f"{question} [{hint}] ").lower()
        return (reply == "y") if default != "yes" else (reply in ("", "y"))

    def _validate_and_parse_slice(self, slice_str: str, max_len: int) -> tuple[list[int], str | None]:
        """
        Validate and parse slice notation with helpful error messages.
        Returns (indices, error_message)
        """
        try:
            # Handle ":" for all items
            if slice_str == ":":
                return list(range(1, max_len + 1)), None
                
            # Parse slice parts
            parts = slice_str.split(':')
            if len(parts) not in (2, 3):
                return [], "Invalid slice format. Use start:end[:step]"
                
            # Convert parts to integers, handling empty values
            start = int(parts[0]) if parts[0] else 1
            end = int(parts[1]) if parts[1] else max_len
            step = int(parts[2]) if len(parts) == 3 and parts[2] else 1
            
            # Validate ranges
            if start < 1 or start > max_len:
                return [], f"Start index must be between 1 and {max_len}"
            if end < 1 or end > max_len:
                return [], f"End index must be between 1 and {max_len}"
            if step < 1:
                return [], "Step must be positive"
                
            # Generate indices
            indices = list(range(start, end + 1, step))
            return indices, None
            
        except ValueError:
            return [], "Invalid numbers in slice"

    def prompt_choose(self,
        question: str, 
        options: list | None = None,
        inputs: list | str = "num",
        allow_multiple: bool = False,
        hide_options: bool = False,
    ) -> str | list[str]:
        """Enhanced choice prompt supporting multiple selections and slicing."""
        print(f"\n{question}")
        
        # If no options provided, just return raw input
        if options is None:
            return input().strip()

        # Handle numbered inputs mode
        if inputs == "num":
            inputs = [str(i) for i in range(1, len(options) + 1)]

        # Display options unless hidden
        if not hide_options:
            for i, option in enumerate(options):
                print(f"{inputs[i]}: {trunc(str(option), 60)}")

        while True:
            response = input().strip()
            
            # Handle multiple selection
            if allow_multiple:
                try:
                    # Handle slice notation
                    if ':' in response:
                        indices, error = self._validate_and_parse_slice(response, len(options))
                        if error:
                            print(f"There's something wrong honey: {error}")
                            continue
                        return [options[i-1] for i in indices]
                    
                    # Handle space-separated numbers
                    nums = response.split()
                    selections = [options[int(n)-1] for n in nums if 0 < int(n) <= len(options)]
                    if selections:
                        return selections
                    
                except (ValueError, IndexError) as e:
                    print(f"There's something wrong honey: {e}")
            
            # Handle single selection
            else:
                try:
                    if response in inputs:
                        idx = inputs.index(response)
                        return options[idx]
                except (ValueError, IndexError):
                    pass
            
            print("Invalid input. Please try again.")