# Secure Code Generation Guidelines for Web+ Code Factory

## 🎯 OVERVIEW

This document defines the exact secure coding patterns and practices that the Web+ Code Factory will implement and enforce. Every piece of generated code must follow these guidelines to ensure production-ready, secure applications.

---

## ✅ FUNDAMENTAL SECURITY PRINCIPLES

### 1. **Never Trust User Input**
- Validate all inputs at entry points
- Sanitize data before processing
- Use parameterized queries for databases
- Implement input length limits
- Escape output appropriately

### 2. **Principle of Least Privilege**
- Grant minimum necessary permissions
- Use role-based access control
- Implement authorization checks
- Limit API access scopes
- Restrict file system access

### 3. **Defense in Depth**
- Multiple security layers
- Input validation + output encoding
- Authentication + authorization
- Rate limiting + monitoring
- Encryption + secure protocols

### 4. **Fail Securely**
- Default to deny access
- Log security events
- Don't expose internal errors
- Graceful degradation
- Secure error messages

---

## 🔒 MANDATORY SECURITY PATTERNS

### Pattern 1: Secure Function Template

**Every function generated must follow this pattern:**

```typescript
async function operationName(input: InputType): Promise<Result<OutputType>> {
  // 1. Input Validation
  const validationResult = validateInput(input, inputSchema);
  if (!validationResult.success) {
    logger.warn('Invalid input received', { 
      operation: 'operationName',
      errors: validationResult.errors 
    });
    return Result.fail(new ValidationError('Invalid input parameters'));
  }

  // 2. Authorization Check (if applicable)
  if (requiresAuth && !isAuthorized(context.user, requiredPermission)) {
    logger.warn('Unauthorized access attempt', { 
      operation: 'operationName',
      userId: context.user?.id 
    });
    return Result.fail(new AuthorizationError('Insufficient permissions'));
  }

  try {
    // 3. Business Logic with Error Handling
    const result = await performOperation(validationResult.data);
    
    // 4. Output Sanitization (if needed)
    const sanitizedResult = sanitizeOutput(result);
    
    // 5. Success Logging
    logger.info('Operation completed successfully', { 
      operation: 'operationName',
      userId: context.user?.id 
    });
    
    return Result.ok(sanitizedResult);
    
  } catch (error) {
    // 6. Error Handling
    logger.error('Operation failed', { 
      operation: 'operationName',
      error: error.message,
      stack: error.stack
    });
    
    // 7. Secure Error Response (no sensitive data)
    if (error instanceof DatabaseError) {
      return Result.fail(new AppError('Database operation failed'));
    } else if (error instanceof ExternalServiceError) {
      return Result.fail(new AppError('External service unavailable'));
    } else {
      return Result.fail(new AppError('Operation failed'));
    }
  }
}
```

### Pattern 2: Secure API Endpoint Template

**Every API endpoint must follow this pattern:**

```typescript
// Route definition with security middleware
app.post('/api/resource/:id',
  rateLimiter({             // 1. Rate limiting
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100,                 // requests per window
    standardHeaders: true,
    legacyHeaders: false
  }),
  authenticateToken,        // 2. Authentication
  validateRequest(schema),  // 3. Input validation
  sanitizeInput,           // 4. Input sanitization
  async (req: AuthenticatedRequest, res: Response) => {
    try {
      // 5. Extract and validate parameters
      const { id } = req.params;
      const userId = req.user.id;
      
      // 6. Authorization check
      const hasAccess = await authService.canAccessResource(userId, id, 'write');
      if (!hasAccess) {
        return res.status(403).json({ 
          error: 'Forbidden',
          message: 'Insufficient permissions to access this resource'
        });
      }

      // 7. Business logic
      const result = await resourceService.updateResource(id, req.body, userId);

      // 8. Success response
      res.status(200).json({
        success: true,
        data: result,
        meta: {
          timestamp: new Date().toISOString(),
          requestId: req.id
        }
      });

    } catch (error) {
      // 9. Error logging (with request context)
      logger.error('API endpoint error', {
        endpoint: '/api/resource/:id',
        method: 'POST',
        userId: req.user?.id,
        requestId: req.id,
        error: error.message
      });

      // 10. Secure error response
      if (error instanceof ValidationError) {
        return res.status(400).json({
          error: 'Bad Request',
          message: 'Invalid input data',
          details: error.details
        });
      } else if (error instanceof NotFoundError) {
        return res.status(404).json({
          error: 'Not Found',
          message: 'Resource not found'
        });
      } else {
        return res.status(500).json({
          error: 'Internal Server Error',
          message: 'An unexpected error occurred',
          requestId: req.id
        });
      }
    }
  }
);
```

### Pattern 3: Secure Database Operations

**Always use parameterized queries:**

```typescript
class UserRepository {
  // ✅ CORRECT - Parameterized query
  async findUserById(id: string): Promise<User | null> {
    const query = `
      SELECT id, email, name, created_at, updated_at 
      FROM users 
      WHERE id = $1 AND deleted_at IS NULL
    `;
    
    const result = await this.db.query(query, [id]);
    return result.rows[0] || null;
  }

  // ✅ CORRECT - Parameterized update with validation
  async updateUser(id: string, updates: Partial<User>): Promise<User> {
    // Validate allowed fields
    const allowedFields = ['name', 'email', 'updated_at'];
    const sanitizedUpdates = Object.keys(updates)
      .filter(key => allowedFields.includes(key))
      .reduce((obj, key) => {
        obj[key] = updates[key];
        return obj;
      }, {} as any);

    if (Object.keys(sanitizedUpdates).length === 0) {
      throw new ValidationError('No valid fields to update');
    }

    // Build dynamic query safely
    const setClause = Object.keys(sanitizedUpdates)
      .map((key, index) => `${key} = $${index + 2}`)
      .join(', ');
    
    const query = `
      UPDATE users 
      SET ${setClause}, updated_at = NOW()
      WHERE id = $1 AND deleted_at IS NULL
      RETURNING id, email, name, created_at, updated_at
    `;
    
    const values = [id, ...Object.values(sanitizedUpdates)];
    const result = await this.db.query(query, values);
    
    if (result.rows.length === 0) {
      throw new NotFoundError('User not found');
    }
    
    return result.rows[0];
  }

  // ❌ WRONG - Never do this (SQL injection vulnerability)
  // async findUserByEmail(email: string): Promise<User | null> {
  //   const query = `SELECT * FROM users WHERE email = '${email}'`;
  //   const result = await this.db.query(query);
  //   return result.rows[0] || null;
  // }
}
```

### Pattern 4: Environment Configuration

**Never hardcode secrets:**

```typescript
// config/environment.ts
import { z } from 'zod';

const envSchema = z.object({
  // Database
  DATABASE_URL: z.string().url(),
  DATABASE_SSL: z.boolean().default(true),
  
  // Authentication
  JWT_SECRET: z.string().min(32),
  JWT_EXPIRES_IN: z.string().default('24h'),
  
  // External Services
  REDIS_URL: z.string().url().optional(),
  SMTP_HOST: z.string().optional(),
  SMTP_PORT: z.number().optional(),
  SMTP_USER: z.string().optional(),
  SMTP_PASS: z.string().optional(),
  
  // Security
  BCRYPT_ROUNDS: z.number().min(10).default(12),
  RATE_LIMIT_WINDOW: z.number().default(15 * 60 * 1000),
  RATE_LIMIT_MAX: z.number().default(100),
  
  // Application
  NODE_ENV: z.enum(['development', 'staging', 'production']),
  PORT: z.number().default(3000),
  LOG_LEVEL: z.enum(['error', 'warn', 'info', 'debug']).default('info')
});

export type Environment = z.infer<typeof envSchema>;

export function loadEnvironment(): Environment {
  const result = envSchema.safeParse(process.env);
  
  if (!result.success) {
    console.error('Environment validation failed:');
    console.error(result.error.format());
    process.exit(1);
  }
  
  return result.data;
}

// ✅ Usage in application
const env = loadEnvironment();

// ❌ NEVER do this:
// const apiKey = "sk-1234567890abcdef";
// const dbPassword = "mypassword123";
```

### Pattern 5: Input Validation Schema

**Comprehensive input validation:**

```typescript
import { z } from 'zod';

// User registration schema
export const userRegistrationSchema = z.object({
  email: z.string()
    .email('Invalid email format')
    .max(255, 'Email too long')
    .transform(email => email.toLowerCase().trim()),
    
  password: z.string()
    .min(8, 'Password must be at least 8 characters')
    .max(128, 'Password too long')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),
    
  name: z.string()
    .min(1, 'Name is required')
    .max(100, 'Name too long')
    .regex(/^[a-zA-Z\s-']+$/, 'Name contains invalid characters')
    .transform(name => name.trim()),
    
  age: z.number()
    .int('Age must be an integer')
    .min(13, 'Must be at least 13 years old')
    .max(120, 'Invalid age')
    .optional(),
    
  preferences: z.object({
    newsletter: z.boolean().default(false),
    notifications: z.boolean().default(true),
    theme: z.enum(['light', 'dark']).default('light')
  }).optional()
});

// API endpoint validation middleware
export function validateRequest(schema: z.ZodSchema) {
  return (req: Request, res: Response, next: NextFunction) => {
    try {
      const validationResult = schema.safeParse(req.body);
      
      if (!validationResult.success) {
        return res.status(400).json({
          error: 'Validation Error',
          message: 'Invalid input data',
          details: validationResult.error.format()
        });
      }
      
      // Replace req.body with validated and transformed data
      req.body = validationResult.data;
      next();
      
    } catch (error) {
      logger.error('Validation middleware error', { error: error.message });
      res.status(500).json({
        error: 'Internal Server Error',
        message: 'Validation failed'
      });
    }
  };
}
```

---

## 🛡️ SECURITY MIDDLEWARE IMPLEMENTATIONS

### 1. Authentication Middleware

```typescript
import jwt from 'jsonwebtoken';
import { User } from '../models/User';

export interface AuthenticatedRequest extends Request {
  user: User;
}

export async function authenticateToken(
  req: Request, 
  res: Response, 
  next: NextFunction
) {
  try {
    // Extract token from Authorization header
    const authHeader = req.headers.authorization;
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (!token) {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Access token required'
      });
    }

    // Verify token
    const decoded = jwt.verify(token, process.env.JWT_SECRET!) as any;
    
    // Get user from database
    const user = await User.findById(decoded.userId);
    if (!user || !user.isActive) {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid or expired token'
      });
    }

    // Attach user to request
    (req as AuthenticatedRequest).user = user;
    next();

  } catch (error) {
    if (error instanceof jwt.JsonWebTokenError) {
      return res.status(401).json({
        error: 'Unauthorized',
        message: 'Invalid token'
      });
    }
    
    logger.error('Authentication middleware error', { error: error.message });
    res.status(500).json({
      error: 'Internal Server Error',
      message: 'Authentication failed'
    });
  }
}
```

### 2. Authorization Middleware

```typescript
export function requirePermission(permission: string) {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    try {
      const user = req.user;
      const hasPermission = await authService.userHasPermission(user.id, permission);
      
      if (!hasPermission) {
        logger.warn('Authorization failed', {
          userId: user.id,
          permission,
          endpoint: req.path
        });
        
        return res.status(403).json({
          error: 'Forbidden',
          message: 'Insufficient permissions'
        });
      }
      
      next();
    } catch (error) {
      logger.error('Authorization middleware error', { error: error.message });
      res.status(500).json({
        error: 'Internal Server Error',
        message: 'Authorization check failed'
      });
    }
  };
}

export function requireResourceOwnership() {
  return async (req: AuthenticatedRequest, res: Response, next: NextFunction) => {
    try {
      const { id } = req.params;
      const userId = req.user.id;
      
      const resource = await getResourceById(id);
      if (!resource) {
        return res.status(404).json({
          error: 'Not Found',
          message: 'Resource not found'
        });
      }
      
      if (resource.ownerId !== userId && !req.user.isAdmin) {
        return res.status(403).json({
          error: 'Forbidden',
          message: 'You can only access your own resources'
        });
      }
      
      next();
    } catch (error) {
      logger.error('Resource ownership check failed', { error: error.message });
      res.status(500).json({
        error: 'Internal Server Error',
        message: 'Ownership verification failed'
      });
    }
  };
}
```

### 3. Rate Limiting Middleware

```typescript
import rateLimit from 'express-rate-limit';
import RedisStore from 'rate-limit-redis';
import Redis from 'redis';

const redisClient = Redis.createClient({
  url: process.env.REDIS_URL
});

// General API rate limiter
export const apiLimiter = rateLimit({
  store: new RedisStore({
    client: redisClient
  }),
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // limit each IP to 100 requests per windowMs
  message: {
    error: 'Too Many Requests',
    message: 'Rate limit exceeded, please try again later'
  },
  standardHeaders: true,
  legacyHeaders: false,
  keyGenerator: (req) => {
    // Use user ID if authenticated, otherwise IP
    const user = (req as AuthenticatedRequest).user;
    return user ? `user:${user.id}` : `ip:${req.ip}`;
  }
});

// Strict rate limiter for sensitive operations
export const strictLimiter = rateLimit({
  store: new RedisStore({
    client: redisClient
  }),
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 5, // limit each user to 5 requests per hour
  message: {
    error: 'Too Many Requests',
    message: 'Too many attempts, please try again later'
  },
  keyGenerator: (req) => {
    const user = (req as AuthenticatedRequest).user;
    return user ? `strict:user:${user.id}` : `strict:ip:${req.ip}`;
  }
});

// Code generation specific limiter
export const codeGenerationLimiter = rateLimit({
  store: new RedisStore({
    client: redisClient
  }),
  windowMs: 60 * 60 * 1000, // 1 hour
  max: 10, // limit to 10 code generations per hour
  message: {
    error: 'Code Generation Limit Exceeded',
    message: 'You have reached the hourly limit for code generation'
  },
  keyGenerator: (req) => {
    const user = (req as AuthenticatedRequest).user;
    return `codegen:user:${user.id}`;
  }
});
```

---

## 🧪 MANDATORY TESTING PATTERNS

### 1. Security Test Template

```typescript
describe('Security Tests', () => {
  describe('SQL Injection Protection', () => {
    test('should prevent SQL injection in user queries', async () => {
      const maliciousInput = "'; DROP TABLE users; --";
      
      const result = await userService.findUserByEmail(maliciousInput);
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('Invalid input');
      
      // Verify table still exists
      const usersCount = await db.query('SELECT COUNT(*) FROM users');
      expect(usersCount.rows[0].count).toBeGreaterThan(0);
    });
  });

  describe('XSS Protection', () => {
    test('should sanitize HTML input', async () => {
      const maliciousInput = '<script>alert("xss")</script>';
      
      const result = await postService.createPost({
        title: 'Test Post',
        content: maliciousInput
      });
      
      expect(result.success).toBe(true);
      expect(result.data.content).not.toContain('<script>');
      expect(result.data.content).toContain('&lt;script&gt;');
    });
  });

  describe('Authentication Bypass', () => {
    test('should reject requests without valid tokens', async () => {
      const response = await request(app)
        .get('/api/protected-resource')
        .expect(401);
      
      expect(response.body.error).toBe('Unauthorized');
    });

    test('should reject expired tokens', async () => {
      const expiredToken = jwt.sign(
        { userId: 'test-user' },
        process.env.JWT_SECRET!,
        { expiresIn: '-1h' }
      );
      
      const response = await request(app)
        .get('/api/protected-resource')
        .set('Authorization', `Bearer ${expiredToken}`)
        .expect(401);
      
      expect(response.body.error).toBe('Unauthorized');
    });
  });

  describe('Authorization Tests', () => {
    test('should prevent access to other users resources', async () => {
      const user1Token = await createUserAndGetToken('user1@example.com');
      const user2Resource = await createResourceForUser('user2@example.com');
      
      const response = await request(app)
        .get(`/api/resources/${user2Resource.id}`)
        .set('Authorization', `Bearer ${user1Token}`)
        .expect(403);
      
      expect(response.body.error).toBe('Forbidden');
    });
  });

  describe('Rate Limiting', () => {
    test('should enforce rate limits', async () => {
      const token = await createUserAndGetToken('test@example.com');
      
      // Make requests up to the limit
      for (let i = 0; i < 100; i++) {
        await request(app)
          .get('/api/test-endpoint')
          .set('Authorization', `Bearer ${token}`)
          .expect(200);
      }
      
      // 101st request should be rate limited
      await request(app)
        .get('/api/test-endpoint')
        .set('Authorization', `Bearer ${token}`)
        .expect(429);
    });
  });
});
```

### 2. Input Validation Test Template

```typescript
describe('Input Validation Tests', () => {
  describe('User Registration', () => {
    test('should accept valid user data', async () => {
      const validUser = {
        email: 'test@example.com',
        password: 'SecurePass123!',
        name: 'Test User'
      };
      
      const result = await userService.registerUser(validUser);
      
      expect(result.success).toBe(true);
      expect(result.data.email).toBe(validUser.email);
    });

    test('should reject invalid email formats', async () => {
      const invalidEmails = [
        'not-an-email',
        '@example.com',
        'test@',
        'test..test@example.com',
        'test@.com'
      ];
      
      for (const email of invalidEmails) {
        const result = await userService.registerUser({
          email,
          password: 'SecurePass123!',
          name: 'Test User'
        });
        
        expect(result.success).toBe(false);
        expect(result.error).toContain('email');
      }
    });

    test('should reject weak passwords', async () => {
      const weakPasswords = [
        'short',           // too short
        'alllowercase',    // no uppercase
        'ALLUPPERCASE',    // no lowercase
        'NoNumbers!',      // no numbers
        'NoSpecial123',    // no special characters
        '12345678'         // common pattern
      ];
      
      for (const password of weakPasswords) {
        const result = await userService.registerUser({
          email: 'test@example.com',
          password,
          name: 'Test User'
        });
        
        expect(result.success).toBe(false);
        expect(result.error).toContain('password');
      }
    });

    test('should sanitize and validate names', async () => {
      const testCases = [
        { input: '  John Doe  ', expected: 'John Doe' },
        { input: 'Jane-Smith', expected: 'Jane-Smith' },
        { input: "O'Connor", expected: "O'Connor" },
        { input: '<script>alert("xss")</script>', shouldFail: true },
        { input: 'A'.repeat(101), shouldFail: true }
      ];
      
      for (const testCase of testCases) {
        const result = await userService.registerUser({
          email: 'test@example.com',
          password: 'SecurePass123!',
          name: testCase.input
        });
        
        if (testCase.shouldFail) {
          expect(result.success).toBe(false);
        } else {
          expect(result.success).toBe(true);
          expect(result.data.name).toBe(testCase.expected);
        }
      }
    });
  });
});
```

### 3. Error Handling Test Template

```typescript
describe('Error Handling Tests', () => {
  describe('Database Connection Failures', () => {
    test('should handle database connection timeouts gracefully', async () => {
      // Mock database timeout
      jest.spyOn(db, 'query').mockRejectedValueOnce(
        new Error('Connection timeout')
      );
      
      const result = await userService.findUserById('test-id');
      
      expect(result.success).toBe(false);
      expect(result.error).not.toContain('Connection timeout');
      expect(result.error).toBe('Database operation failed');
    });

    test('should not expose database errors to users', async () => {
      jest.spyOn(db, 'query').mockRejectedValueOnce(
        new Error('FATAL: database "app" does not exist')
      );
      
      const response = await request(app)
        .get('/api/users/test-id')
        .set('Authorization', `Bearer ${validToken}`)
        .expect(500);
      
      expect(response.body.error).toBe('Internal Server Error');
      expect(response.body.message).not.toContain('database');
      expect(response.body.message).not.toContain('FATAL');
    });
  });

  describe('External Service Failures', () => {
    test('should handle external API failures', async () => {
      // Mock external service failure
      jest.spyOn(emailService, 'sendEmail').mockRejectedValueOnce(
        new Error('SMTP server unreachable')
      );
      
      const result = await userService.sendWelcomeEmail('test@example.com');
      
      expect(result.success).toBe(false);
      expect(result.error).toBe('Email service unavailable');
    });
  });

  describe('Resource Cleanup', () => {
    test('should close database connections on error', async () => {
      const mockConnection = {
        query: jest.fn().mockRejectedValue(new Error('Query failed')),
        release: jest.fn()
      };
      
      jest.spyOn(db, 'getConnection').mockResolvedValueOnce(mockConnection);
      
      await expect(
        userService.performComplexDatabaseOperation('test-data')
      ).rejects.toThrow();
      
      expect(mockConnection.release).toHaveBeenCalled();
    });
  });
});
```

---

## 📋 CODE GENERATION QUALITY CHECKLIST

Every piece of generated code must pass this checklist:

### ✅ Security Checklist
- [ ] All user inputs are validated with appropriate schemas
- [ ] No hardcoded secrets or credentials
- [ ] SQL queries use parameterization
- [ ] HTML output is properly escaped
- [ ] Authentication checks are implemented
- [ ] Authorization checks are implemented
- [ ] Rate limiting is applied to sensitive endpoints
- [ ] Error messages don't expose sensitive information
- [ ] Logging doesn't include sensitive data
- [ ] File operations have proper path validation

### ✅ Error Handling Checklist
- [ ] All async operations are wrapped in try-catch
- [ ] Specific error types are defined and used
- [ ] Error responses are consistent and secure
- [ ] Resources are properly cleaned up on errors
- [ ] Errors are logged with appropriate context
- [ ] Graceful degradation is implemented
- [ ] Timeouts are set for external operations

### ✅ Testing Checklist
- [ ] Unit tests cover happy path scenarios
- [ ] Unit tests cover error scenarios
- [ ] Security tests verify protection mechanisms
- [ ] Integration tests verify end-to-end functionality
- [ ] Performance tests verify acceptable response times
- [ ] Test coverage is at least 80%

### ✅ Code Quality Checklist
- [ ] Functions have single responsibility
- [ ] Variable and function names are descriptive
- [ ] Code follows language-specific conventions
- [ ] No unused imports or variables
- [ ] Proper type annotations (TypeScript)
- [ ] Documentation comments for public APIs
- [ ] Environment variables are properly typed

### ✅ Performance Checklist
- [ ] Database queries are optimized
- [ ] Proper indexing is considered
- [ ] Caching is implemented where appropriate
- [ ] Memory usage is reasonable
- [ ] Response times are within acceptable limits
- [ ] Resource usage is monitored

---

These guidelines ensure that every piece of code generated by the Web+ Code Factory is secure, maintainable, and production-ready. The patterns and templates provided here should be used as the foundation for all code generation activities.