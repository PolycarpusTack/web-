# Stack Trace Analysis Guide

This document provides guidance on how to capture, analyze, and share stack traces with Claude for effective bug fixing.

## Capturing Stack Traces

### JavaScript/Node.js

To capture a full stack trace in JavaScript:

```javascript
try {
  // Code that might throw an error
} catch (error) {
  console.error('Full error:', error);
  console.error('Stack trace:', error.stack);
}
```

For Node.js, you can use:

```bash
# Run with full stack traces
node --stack-trace-limit=100 your-script.js
```

### Python

```python
import traceback

try:
    # Code that might raise an exception
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()
```

### Java

```java
try {
    // Code that might throw an exception
} catch (Exception e) {
    e.printStackTrace();
}
```

## Reading Stack Traces

A stack trace typically includes:

1. **Exception Type**: The kind of error that occurred
2. **Error Message**: Description of what went wrong
3. **Call Stack**: The sequence of function calls leading to the error
   - Each line shows a function/method call
   - Includes file names, line numbers, and sometimes column numbers
   - Top of the stack is where the error occurred
   - Bottom of the stack is where execution started

## Analyzing Stack Traces with Claude

When sharing stack traces with Claude, follow these steps:

1. **Clean the Stack Trace**:
   - Remove sensitive information (API keys, passwords)
   - Include the full trace when possible
   - Format with proper code blocks

2. **Provide Context**:
   - What were you trying to do?
   - Which line in your code corresponds to the error?
   - Have you made recent changes to the code?

3. **Ask Specific Questions**:
   - What is causing this error?
   - How can I fix this specific issue?
   - Is there a pattern or common mistake in this type of error?

## Example Stack Trace Analysis Request

```
Claude, I'm getting the following error in my Node.js application:

## Stack Trace
```javascript
TypeError: Cannot read property 'name' of undefined
    at UserService.getUserDetails (/app/services/UserService.js:45:23)
    at processTicksAndRejections (internal/process/task_queues.js:95:5)
    at async Router.getUser (/app/routes/user.js:32:12)
    at async /app/middleware/errorHandler.js:12:5
```

## Context
I'm trying to retrieve user details from the database. The error happens when a user ID is provided that doesn't exist in the database. However, I expect it to return null rather than throwing an error.

## Relevant Code
```javascript
// UserService.js
async getUserDetails(userId) {
  const user = await this.db.findUserById(userId);
  return {
    id: user.id,
    name: user.name,
    email: user.email
  };
}
```

How should I modify this code to handle the case where the user doesn't exist?
```

## Tips for Effective Stack Trace Analysis

1. **Look for the Root Cause**:
   - The actual error might be several levels up the stack
   - Pay attention to your own code, not just library code

2. **Check for Common Patterns**:
   - Null/undefined references
   - Type mismatches
   - Asynchronous issues
   - Resource not found

3. **Isolate the Problem**:
   - Create a minimal reproduction case
   - Test one component at a time

4. **Document the Solution**:
   - Record what fixed the issue
   - Add tests to prevent regression
   - Update documentation if needed

## Resources

- [MDN Web Docs: Error](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error)
- [Python Traceback Documentation](https://docs.python.org/3/library/traceback.html)
- [Java Exception Handling](https://docs.oracle.com/javase/tutorial/essential/exceptions/)