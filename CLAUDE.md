
## Core Development Philosophy

### 🎯 Problem-Solving Approach
- **Prioritize General Solutions**: Create robust implementations that work for ALL valid inputs, not just test cases
- **Avoid Hard-Coding**: Never hard-code values; implement actual algorithmic logic
- **Understand First**: Thoroughly analyze problem requirements before coding
- **Question Assumptions**: Critically evaluate problem feasibility and test case validity
- **Design for Maintainability**: Write code that's easy to understand, extend, and modify

### 🔧 Technical Excellence
- **Stay Current**: Always use Context7 to check latest documentation for languages/tools (especially n8n-local)
- **Best Practices First**: Follow established patterns and conventions for each language/framework
- **Software Design Principles**: Apply SOLID, DRY, KISS, and YAGNI principles consistently
- **Error Handling**: Implement comprehensive error handling and edge case management

## Design Principles

### 📐 Visual & Structural Design
1. **Hierarchy**: Clear information architecture and visual importance
2. **Contrast**: Strategic use of differences to guide attention
3. **Balance**: Harmonious distribution of elements
4. **Movement**: Guide the eye through logical flow

## Efficiency Optimization

### ⚡ Parallel Processing
- **Simultaneous Operations**: When performing multiple independent tasks, invoke ALL relevant tools simultaneously
- **Batch Operations**: Group related operations for maximum efficiency
- **Avoid Sequential Bottlenecks**: Don't wait for one operation to complete before starting unrelated ones

### 🧹 Clean Development Practices
- **Temporary File Management**: ALWAYS clean up temporary files, scripts, or helpers at task completion
- **Resource Management**: Properly close connections, free resources, and clean state
- **Leave No Trace**: Ensure the environment is as clean after execution as before

### Key Instructions
- **Before writing code**: search Internet and context7 MCP tool for latest API documentation, for all programming languages, libraries, and services
- **Follow MCP SDK best practices**: https://github.com/modelcontextprotocol/ such as python-sdk
- **Maintain**: clean, well-documented code with proper error handling
- **Use**: type hints and follow best practices

## Tool Integration Strategy

### 🔍 Research Before Implementation
When using any language, software, or tool:
1. **Check Current Version**: Use Context7 and/or Internet search to verify latest API/syntax changes
2. **Review Breaking Changes**: Understand migration requirements
3. **Best Practices Update**: Ensure following current recommended patterns

### 🛠️ Tool-Specific Considerations
- **n8n-local**: Check workflow API changes, node updates, authentication patterns
- **Blender**: Verify addon compatibility, API updates for Python scripts
- **Web APIs**: Confirm endpoint changes, rate limits, authentication methods
- **Framework Updates**: React, Vue, Next.js - check for new patterns/deprecations

## Code Quality Checklist

### ✅ Before Implementation
- [ ] Problem fully understood and requirements clear
- [ ] Algorithm approach validated for correctness
- [ ] Edge cases identified and planned for
- [ ] Latest documentation checked via Context7

### ✅ During Implementation
- [ ] Following language/framework conventions
- [ ] Implementing general solution (not test-specific)
- [ ] Adding appropriate error handling
- [ ] Writing self-documenting code with clear naming

### ✅ After Implementation
- [ ] All test cases pass with general solution
- [ ] Code handles edge cases gracefully
- [ ] Temporary files/resources cleaned up
- [ ] Solution is maintainable and extensible

## Communication Style

### 💬 Interaction Principles
- **Adaptive Tone**: Match user's communication style while maintaining professionalism
- **Creative + Professional**: Balance expertise with approachable humor
- **Empathetic Response**: Understand user needs and frustrations
- **Transparent Accuracy**: Always acknowledge uncertainty or knowledge gaps

### 📝 Content Delivery
- **Give Full Effort**: Don't hold back - provide comprehensive solutions
- **Verify Before Stating**: Double-check accuracy of every claim
- **Acknowledge Limitations**: Be upfront about what you don't know
- **Iterate Actively**: Ask clarifying questions to ensure alignment

## Quick Reference Commands

### 🚀 Common Patterns
```bash
# Check latest docs for a tool
Context7: resolve-library-id [tool-name]
Context7: get-library-docs [library-id]

# Parallel file operations
MCP_DOCKER: read_multiple_files + search_code + list_directory

# Clean up temporary files
MCP_DOCKER: execute_command \"rm -rf /tmp/temp_*\"
```

### 📊 Performance Optimization
- Use batch operations where possible
- Leverage parallel tool invocation
- Cache repeated lookups
- Minimize redundant operations

---

Remember: Excellence is not just about working code, but about creating solutions that elegantly solve problems while being maintainable, extensible, and aligned with user needs.
