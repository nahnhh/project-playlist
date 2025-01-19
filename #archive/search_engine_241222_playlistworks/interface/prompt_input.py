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

    def prompt_choose(self,
        question: str, 
        displayed_options: list | None = None, 
        inputs: list | str = "num",  # Default to numbered inputs
        allow_multiple: bool = False,
    ) -> str | list[str]:
        """Enhanced choice prompt supporting multiple selections and letter inputs."""
        print(f"\n{question}")
        
        # If no options provided, just return raw input
        if displayed_options is None:
            return input().strip()

        # Handle numbered inputs mode
        if inputs == "num":
            inputs = [str(i) for i in range(1, len(displayed_options) + 1)]

        # Display options
        for i, option in enumerate(displayed_options):
            print(f"{inputs[i]}: {trunc(str(option), 60)}")

        while True:
            response = input().strip()
            
            # Handle multiple selection
            if allow_multiple:
                try:
                    nums = response.split()
                    selections = [displayed_options[int(n)-1] for n in nums if 0 < int(n) <= len(displayed_options)]
                    if selections:
                        return selections
                except (ValueError, IndexError):
                    pass
            
            # Handle single selection
            else:
                try:
                    if response in inputs:
                        idx = inputs.index(response)
                        return displayed_options[idx]
                except (ValueError, IndexError):
                    pass
            
            print("Invalid input. Please try again.")