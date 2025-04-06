# tools/registry.py

class ToolRegistry:
    """
    A registry for all available tools that can be used by the agent.
    Allows for dynamic tool discovery and execution.
    """

    def __init__(self):
        self.tools = {}
        self.descriptions = {}

    def register(self, name, function, description=None):
        """
        Register a tool function with the registry.

        Args:
            name (str): The name of the tool
            function (callable): The function to call when tool is invoked
            description (str, optional): A description of what the tool does
        """
        self.tools[name] = function
        if description:
            self.descriptions[name] = description

    def get_tool(self, name):
        """
        Get a tool function by name.

        Args:
            name (str): The name of the tool to retrieve

        Returns:
            callable: The tool function

        Raises:
            KeyError: If the tool doesn't exist
        """
        if name not in self.tools:
            raise KeyError(f"Tool '{name}' not found in registry")
        return self.tools[name]

    def execute(self, name, *args, **kwargs):
        """
        Execute a tool by name with the given arguments.

        Args:
            name (str): The name of the tool to execute
            *args: Positional arguments to pass to the tool
            **kwargs: Keyword arguments to pass to the tool

        Returns:
            The result of the tool execution

        Raises:
            KeyError: If the tool doesn't exist
        """
        tool = self.get_tool(name)
        return tool(*args, **kwargs)

    def list_tools(self):
        """
        List all available tools.

        Returns:
            dict: A dictionary of tool names and their descriptions
        """
        result = {}
        for name in self.tools:
            desc = self.descriptions.get(name, "No description available")
            result[name] = desc
        return result

    def get_tool_descriptions_formatted(self):
        """
        Get a formatted string of all tool descriptions for use in prompts.

        Returns:
            str: A formatted string of tool names and descriptions
        """
        lines = []
        for name, desc in self.descriptions.items():
            lines.append(f"- {name}: {desc}")
        return "\n".join(lines)
