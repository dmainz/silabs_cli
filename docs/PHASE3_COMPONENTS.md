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
- [ ] Save configuration to project .slcp file

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

## Implementation Notes
- Component discovery requires slc-cli integration
- menuconfig needs curses library for terminal UI
- Configuration files use Silabs native .slcp/.slcc YAML format
- Dependencies must be resolved before component installation

## Status: BASIC STRUCTURE COMPLETE
Phase 3.1-3.3 basic command structure implemented. Full slc-cli integration and .slcp/.slcc file handling still needed.