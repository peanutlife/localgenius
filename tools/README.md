Tools Registry for LocalGenius
Overview
The Tools Registry provides a flexible and extensible way to register, discover, and execute tools within the LocalGenius agent. It serves as a central repository for all capabilities the agent can use during task execution.

Core Components
ToolRegistry Class
The central component is the ToolRegistry class which:

Stores references to tool functions
Provides descriptions for each tool
Enables dynamic execution of tools by name
Supports formatted output for LLM context
Tool Categories
The Tools Registry organizes tools into several categories:

Core Tools
run_code: Execute Python code snippets
read_file / write_file: File operations
run_shell: Execute shell commands
list_files: Get directory listings
Git Tools
git_status, git_diff, git_add, etc: Git operations
View repository status, make commits, clone repos
Web Tools
fetch_url: Make HTTP requests
download_file: Save remote files locally
scrape_page: Extract content from web pages
Database Tools
execute_query: Run SQL queries
import_csv_to_db: Import data from CSV files
export_query_to_csv: Export query results to CSV
Using the Tools Registry
Accessing the Registry
python
from tools import get_registry

# Get the registry instance
tools = get_registry()

# Get a list of all available tools
tool_list = tools.list_tools()
Executing Tools
python
# Execute a tool by name with parameters
result = tools.execute("read_file", path="path/to/file.txt")

# Or get the function and call it directly
read_file_func = tools.get_tool("read_file")
content = read_file_func("path/to/file.txt")
Adding New Tools
To add a new tool category:

Create a new file in the tools directory (e.g., my_tools.py)
Implement your tool functions
Add a registration function like:
python
def register_my_tools(registry):
    registry.register(
        "my_tool_name",
        my_tool_function,
        "Description of what the tool does"
    )
    # Add more tools...
    return registry
Update tools/__init__.py to import and call your registration function
Integration with LLM Planning
The Tools Registry integrates with the TaskPlanner by:

Providing tool descriptions to the LLM for awareness of capabilities
Parsing execution plans that specify which tools to use
Executing the specified tools with parameters
Tracking results for job history and debugging
Available Tools
Core Tools
run_code: Execute Python code and return the output
read_file: Read content from a file at the specified path
write_file: Write content to a file at the specified path
run_shell: Execute a shell command and return stdout, stderr, and return code
list_files: List all files in a specified directory
file_exists: Check if a file exists at the specified path
read_json: Read and parse a JSON file
write_json: Write data to a JSON file
Git Tools
git_status: Get the current Git repository status
git_diff: Get the diff of changes in the repository
git_add: Add files to Git staging area
git_commit: Commit staged changes with a message
git_log: Get the Git commit history
git_clone: Clone a Git repository
git_checkout: Checkout a Git branch
git_branch: List Git branches
Web Tools
fetch_url: Fetch content from a URL
download_file: Download a file from a URL to a specified path
scrape_page: Scrape content from a webpage
validate_url: Validate if a string is a properly formatted URL
Database Tools
execute_query: Execute a SQL query on a SQLite database
create_database: Create a new SQLite database
import_csv_to_db: Import a CSV file into a SQLite database
export_query_to_csv: Export query results to a CSV file
get_table_schema: Get the schema of a table
list_tables: List all tables in a SQLite database
Next Steps
Future enhancements planned for the Tools Registry:

Tool Parameter Validation: Add type checking and validation
Error Handling: Improve error reporting and recovery
Authentication: Add support for tools requiring authentication
Tool Dependencies: Handle tools that depend on other tools
Tool Metrics: Track tool usage and performance statistics
