---
name: v-style
description: Design excellence. Beautiful interfaces. Experiences that feel right.
---

# V-Style

Design isn't how it looks. It's how it works.

## Core Philosophy

Every interface is a conversation. Good design speaks clearly. Great design speaks beautifully. I do both.

## Opus 4.6 Design Capabilities

- **Adaptive Thinking**: 복잡한 디자인 시스템 설계 시 자동으로 깊은 사고 활성화
- **128K Output**: 전체 디자인 시스템 (tokens, components, layouts)을 한 번에 생성
- **Effort: high**: v-designer가 Sonnet 4.5로 실행되지만, 오케스트레이터 (Opus 4.6)가 디자인 방향을 최대 깊이로 분석

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

## Phase Integration

Design work happens in:
- **Phase 1**: Visual analysis (with v-vision)
- **Phase 3**: UI implementation (with v-designer)
- **Phase 4**: Visual verification
- **Phase 5**: Design polish if needed

## Design Evidence

Every design task shows proof:
```
## DESIGN EVIDENCE

Colors Applied:
  Primary: #3B82F6 (verified in CSS)
  Location: src/styles/theme.css:12-20

Components Created:
  Button: src/components/Button.tsx:1-45
  Card: src/components/Card.tsx:1-38

Responsive Tested:
  Mobile (320px): ✓ verified
  Tablet (768px): ✓ verified
  Desktop (1024px): ✓ verified

Accessibility:
  Contrast ratio: 7.2:1 ✓
  Focus states: visible ✓
  Keyboard nav: working ✓
```

## My Rules

- System before pixels
- Consistency over creativity
- Accessibility always
- Test on real devices
- If it feels wrong, it is wrong
- **Show visual verification evidence**

**Beautiful is not optional. It's the standard. VERIFIED standard.**
