# Silabs CLI Implementation Plan

## Overview
Transform `silabs_cli_manager.py` into `silabs.py` - a comprehensive command-line interface for Simplicity Studio 6 development, inspired by ESP-IDF's `idf.py` architecture.

---

## Phase 1: Core Infrastructure & Renaming

### 1.1 Rename and Restructure
- [✓] Rename `silabs_cli_manager.py` → `silabs.py`
- [✓] Refactor into modular structure:
  - `silabs.py` - Main CLI entry point
  - `silabs/` directory with submodules:
    - `__init__.py`
    - `config.py` - Configuration (TOML parsing)
    - `tools.py` - Tool path management
    - `commands.py` - Command definitions
    - `extensions.py` - Extension system
    - `utils.py` - Utility functions

### 1.2 CLI Framework Setup
- [✓] Replace curses menu with Click CLI framework
- [✓] Implement argument parsing for commands and options
- [✓] Add global options: `-C` (project dir), `-B` (build dir), `-v` (verbose)
- [✓] Create help system (`silabs.py --help`, `silabs.py <command> --help`)

### 1.3 Configuration Management
- [✓] Enhance TOML parsing to handle `tools.json` lookup
- [✓] Implement dynamic tool path resolution via `slt where <tool>`
- [✓] Support `.slconf` file discovery in project directory
- [✓] Add configuration caching for performance

### 1.4 Environment Setup
- [✓] Integrate Silabs tool paths into subprocess environment
- [✓] Set up proper PATH ordering (Java, GCC, CMake, Ninja)
- [✓] Support environment variable overrides
- [✓] Create environment validation checks

---

## Phase 2: Basic Commands

### 2.1 Project Management
- [✓] `silabs.py create-project <name>` - Create new Silabs project
- [✓] `silabs.py list-projects` - List available projects
- [✓] `silabs.py set-target <target>` - Select target device
- [✓] `silabs.py list-targets` - Show available targets

### 2.2 Build Operations
- [✓] `silabs.py build` - Build project (with CMake + Ninja)
- [✓] `silabs.py clean` - Remove build artifacts
- [✓] `silabs.py fullclean` - Delete entire build directory
- [✓] `silabs.py reconfigure` - Force CMake reconfiguration

### 2.3 Device Operations
- [✓] `silabs.py flash [app|bootloader]` - Flash to device
- [✓] `silabs.py monitor` - Start serial monitor
- [✓] `silabs.py erase` - Erase device flash

### 2.4 Information Commands
- [✓] `silabs.py size` - Show binary size information
- [✓] `silabs.py docs` - Open documentation
- [✓] `silabs.py version` - Show tool versions
- [✓] `silabs.py config` - Display project configuration

---

## Phase 3: Component Configuration

### 3.1 Component Discovery & Listing
- [✓] Implement `slc component list` integration
- [✓] Parse available components from SDK
- [✓] Store component metadata (description, dependencies, etc.)
- [✓] Support filtering by category
- [✓] `silabs.py component list` - List available components

### 3.2 Kconfig-Style UI
- [✓] `silabs.py menuconfig` - Interactive component configuration
- [ ] Implement curses-based navigation for component selection
- [ ] Show component descriptions and dependencies
- [ ] Track selected/deselected components
- [ ] Save configuration to project

### 3.3 Component Management
- [✓] `silabs.py component install <name>` - Install specific component
- [✓] `silabs.py component remove <name>` - Remove component
- [✓] `silabs.py component info <name>` - Show component details
- [ ] Validate dependencies before installation

### 3.4 Configuration Files
- [ ] Support `.slcp` file generation and editing (YAML format)
- [ ] Handle `.slcc` component configuration files
- [ ] Backup old configs before modifications (`.slcp.old`)
- [ ] Integrate with `slc generate` and project configuration

---

## Phase 4: Command Chaining & Automation

### 4.1 Command Execution
- [ ] Parse multiple commands from single invocation
- [ ] Implement dependency ordering (build before flash, etc.)
- [ ] Allow command pipelines: `silabs.py clean build flash monitor`
- [ ] Add `--check` option to verify before executing

### 4.2 Build Profiles
- [ ] Support CMakePresets.json for multiple configurations
- [ ] Implement `--preset <name>` option
- [ ] Allow preset-specific build directories and settings
- [ ] Auto-select default preset if available

### 4.3 Parallel Operations
- [ ] Support multi-target builds if applicable
- [ ] Optimize incremental builds
- [ ] Add build caching support (ccache-style)

---

## Phase 5: Advanced Features

### 5.1 Extension System
- [ ] Create extension discovery mechanism
- [ ] Support `silabs_ext.py` files in projects/components
- [ ] Implement extension registration and loading
- [ ] Allow extensions to add custom commands
- [ ] Document extension API

### 5.2 Error Handling & Hints
- [ ] Create error message database (YAML format)
- [ ] Implement automatic error matching
- [ ] Provide actionable hints for common errors
- [ ] Add `--no-hints` option to disable hints
- [ ] Capture and log build output

### 5.3 Shell Integration
- [ ] Implement bash/zsh autocompletion
- [ ] Generate completion scripts
- [ ] Support argument suggestion
- [ ] Make completion discoverable in docs

### 5.4 Argument Files
- [ ] Support `@file` syntax for argument files
- [ ] Allow configuration profiles via files
- [ ] Support multiple `@file` arguments
- [ ] Validate and expand arguments

---

## Phase 6: Development Workflow Tools

### 6.1 Build Analysis
- [ ] `silabs.py size-components` - Per-component size breakdown
- [ ] `silabs.py size-files` - Per-file size analysis
- [ ] Support multiple output formats (text, csv, json)
- [ ] Generate size reports and trends

### 6.2 Device Management
- [ ] `silabs.py list-devices` - Detect connected devices
- [ ] `silabs.py device-info` - Show device details
- [ ] `silabs.py select-device <port>` - Choose device
- [ ] Support multiple simultaneous devices

### 6.3 Debugging Support
- [ ] `silabs.py gdb` - Start GDB session
- [ ] `silabs.py openocd` - Launch OpenOCD
- [ ] Integration with VSCode debugger
- [ ] Support for JTAG/SWD protocols

---

## Phase 7: Documentation & Testing

### 7.1 Documentation
- [ ] Write comprehensive README with examples
- [ ] Create command reference documentation
- [ ] Add troubleshooting guide
- [ ] Document extension development
- [ ] Create quick-start tutorial

### 7.2 Testing
- [ ] Unit tests for config parsing
- [ ] Integration tests for command execution
- [ ] Mock tests for tool invocation
- [ ] Test error message matching
- [ ] Performance benchmarks

### 7.3 CI/CD Integration
- [ ] Support for GitHub Actions workflows
- [ ] Gitlab CI templates
- [ ] Jenkins integration examples
- [ ] Environment matrix testing

---

## Phase 8: Polish & Distribution

### 8.1 Performance Optimization
- [ ] Profile and optimize hot paths
- [ ] Implement caching for tool discovery
- [ ] Lazy-load extensions
- [ ] Optimize subprocess calls

### 8.2 User Experience
- [ ] Add progress bars for long operations
- [ ] Colored output for status/warnings/errors
- [ ] Interactive prompts where appropriate
- [ ] Quiet mode (`-q`) and verbose mode (`-v`)

### 8.3 Packaging & Distribution
- [ ] Create setup.py/pyproject.toml
- [ ] Package as pip-installable module
- [ ] Support for Docker distribution
- [ ] Create installation script for Silabs
- [ ] Version management and updates

---

## High-Priority Quick Wins (MVP)

These tasks should be completed first for a working MVP:

1. ✅ Rename file to `silabs.py`
2. ✅ Implement Click CLI framework
3. ✅ Add basic commands: `build`, `clean`, `flash`, `monitor`
4. ✅ Implement command chaining
5. ✅ Add help system
6. ✅ Config file parsing enhancement
7. ⏳ Basic `menuconfig` component selection
8. ⏳ Error message hints system

---

## Dependencies & Tools

- **Click** - CLI framework (`pip install click`)
- **PyYAML** - For hints database
- **pyserial** - For serial monitor
- **toml** or **tomli** - TOML parsing (already in stdlib for Python 3.11+)
- **curses** - Terminal UI (stdlib)
- Existing: CMake, Ninja, GCC, Commander (Silabs-managed)

---

## Timeline Estimate

- **Phase 1-2**: 2-3 weeks (Core infrastructure)
- **Phase 3**: 1-2 weeks (Component configuration)
- **Phase 4**: 1 week (Command chaining)
- **Phase 5-6**: 2-3 weeks (Advanced features)
- **Phase 7-8**: 1-2 weeks (Polish & release)

**Total: 8-13 weeks for full implementation**

---

## Success Criteria

- [ ] `silabs.py --help` shows all available commands
- [ ] `silabs.py build flash monitor` completes workflow in single invocation
- [ ] `silabs.py menuconfig` provides interactive component selection
- [ ] Extension system loads custom commands from projects
- [ ] Auto-completion works in bash/zsh/fish
- [ ] Error hints provide actionable solutions
- [ ] All major commands have comprehensive help text
- [ ] Tool integrates seamlessly with VSCode