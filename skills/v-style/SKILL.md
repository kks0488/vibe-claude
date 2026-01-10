---
name: v-style
description: Design excellence. Beautiful interfaces. Experiences that feel right.
---

# V-Style

Design isn't how it looks. It's how it works.

## Core Philosophy

Every interface is a conversation. Good design speaks clearly. Great design speaks beautifully. I do both.

## The Design Process

### 1. Understand the Context

Before any visual decision:
- Who uses this?
- What are they trying to do?
- How do they feel?
- What's the environment?

### 2. Choose a Direction

Commit to a bold aesthetic. Middle-ground is forgettable.

| Direction | Characteristics |
|-----------|-----------------|
| Minimal | Lots of white space, essential only |
| Bold | Strong colors, dramatic typography |
| Soft | Rounded corners, gentle gradients |
| Technical | Monospace, dark mode, precise |
| Playful | Bright colors, animations, personality |
| Luxurious | Rich textures, subtle animations |

### 3. Build the System

```css
/* Colors */
:root {
  --bg: #...;
  --surface: #...;
  --primary: #...;
  --primary-hover: #...;
  --text: #...;
  --text-muted: #...;
  --border: #...;
  --success: #...;
  --error: #...;
}

/* Spacing */
--space-xs: 4px;
--space-sm: 8px;
--space-md: 16px;
--space-lg: 24px;
--space-xl: 32px;
--space-2xl: 48px;

/* Typography */
--font-sans: '...', sans-serif;
--font-mono: '...', monospace;
--text-sm: 0.875rem;
--text-base: 1rem;
--text-lg: 1.25rem;
--text-xl: 1.5rem;
--text-2xl: 2rem;

/* Shadows */
--shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
--shadow-md: 0 4px 6px rgba(0,0,0,0.1);
--shadow-lg: 0 10px 15px rgba(0,0,0,0.1);

/* Transitions */
--transition-fast: 0.1s ease-out;
--transition-normal: 0.2s ease-out;
--transition-slow: 0.3s ease-out;
```

## Component Standards

### Buttons
```css
.button {
  padding: var(--space-sm) var(--space-md);
  border-radius: 8px;
  font-weight: 500;
  transition: all var(--transition-fast);
}

.button:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}
```

### Cards
```css
.card {
  background: var(--surface);
  border-radius: 12px;
  padding: var(--space-lg);
  box-shadow: var(--shadow-sm);
}
```

### Forms
```css
.input {
  padding: var(--space-sm) var(--space-md);
  border: 1px solid var(--border);
  border-radius: 8px;
  transition: border-color var(--transition-fast);
}

.input:focus {
  border-color: var(--primary);
  outline: none;
  box-shadow: 0 0 0 3px rgba(primary, 0.1);
}
```

## Accessibility (Non-Negotiable)

- Contrast ratio ≥ 4.5:1 for text
- Focus states visible
- Keyboard navigable
- Screen reader friendly
- Color not the only indicator

## Anti-Patterns

| Never | Instead |
|-------|---------|
| Arial, Times | Distinctive fonts |
| Pure black (#000) | Soft black (#1a1a1a) |
| Hard shadows | Soft, layered shadows |
| No transitions | Subtle animations |
| Cramped spacing | Generous breathing room |

## My Rules

- System before pixels
- Consistency over creativity
- Accessibility always
- Test on real devices
- If it feels wrong, it is wrong

**Beautiful is not optional. It's the standard.**
