# n8n Expression Syntax Cheatsheet

## Basic Syntax

```javascript
// Reference current node's input data
$json.fieldName
$json['field-with-colon']
$json.arrayField[0]
$json.nested.object.field

// Reference other nodes
$('Node Name').item.json.fieldName
$('Node Name').first().json.fieldName
$('Node Name').all()[0].json.fieldName

// Workflow static data (persists across runs, lost on restart)
$getWorkflowStaticData('global').key
$getWorkflowStaticData('node').key
```

## String Operations

```javascript
// Template literals (use backticks)
`Title: {{$json.title}} - Link: {{$json.link}}`

// Concatenation
$json.firstName + ' ' + $json.lastName

// Ternary
$json.published ? 'Published' : 'Draft'

// Nullish coalescing
$json.description ?? $json.excerpt ?? 'No description'

// Optional chaining
$json.author?.name ?? 'Unknown'

// String methods
$json.title.toUpperCase()
$json.title.toLowerCase()
$json.title.trim()
$json.title.substring(0, 100)
$json.title.replace(/[^a-zA-Z0-9]/g, '-')
```

## Array Operations

```javascript
// Map
$json.tags.map(t => t.name).join(', ')

// Filter
$json.items.filter(i => i.published).length

// Find
$json.items.find(i => i.id === '123')

// Some / Every
$json.items.some(i => i.featured)
$json.items.every(i => i.published)

// Join
$json.categories.join(' | ')
```

## Object Operations

```javascript
// Keys / Values / Entries
Object.keys($json)
Object.values($json)
Object.entries($json)

// Merge
{ ...$json, newField: 'value' }

// Pick / Omit (manual)
{ title: $json.title, link: $json.link }
```

## Date Operations

```javascript
// Current date
$now

// Parse date string
new Date($json.pubDate).toISOString()

// Format (requires moment.js or luxon - check n8n version)
// $now.format('YYYY-MM-DD HH:mm:ss')

// Date math
$now.minus(1, 'day')
$now.plus(7, 'days')

// Compare
new Date($json.pubDate) > new Date($getWorkflowStaticData('global').lastRun)
```

## Conditional Logic

```javascript
// IF node condition (returns boolean)
$json.field === 'value'
$json.field !== ''
$json.field > 10
$json.arrayField.length > 0
$json.field?.includes('keyword')

// In Function node (full JS)
if ($json.published) {
  return [{ json: { ...$json, status: 'live' } }];
}
return [{ json: { ...$json, status: 'draft' } }];
```

## JSON Parsing

```javascript
// Parse JSON string field
JSON.parse($json.jsonStringField)

// Stringify
JSON.stringify($json.objectField)
```

## Math

```javascript
$json.price * 1.1
$json.quantity * $json.unitPrice
Math.round($json.rating * 10) / 10
```

## n8n-Specific Variables

| Variable | Description |
|----------|-------------|
| `$json` | Current item's JSON data |
| `$parameter` | Node parameter values |
| `$node` | Current node info |
| `$workflow` | Workflow info |
| `$credentials` | Credential values (use in expressions only) |
| `$getWorkflowStaticData()` | Persistent key-value store |
| `$runIndex` | Current run index (0-based) |
| `$itemIndex` | Current item index in batch |

## Expression Editor Tips

1. **Autocomplete**: Type `$` → see available variables
2. **Drag-drop**: Drag fields from left panel into expression
3. **Preview**: Shows evaluated result for first item
4. **Error handling**: Wrap in try/catch in Function node

## Common Patterns for This Project

```javascript
// Get title safely
$json.title?.[0] || $json['dc:title']?.[0] || 'Untitled'

// Get description (prefer full content)
$json['content:encoded']?.[0] || $json.description?.[0] || $json.summary?.[0] || ''

// Get link
$json.link?.[0] || $json.guid?.[0]?._ || $json.id?.[0] || ''

// Check if new (dedupe)
const posted = $getWorkflowStaticData('global').posted || [];
const isNew = !posted.includes($json.link?.[0]);

// Build Gumroad create command arguments
`products create --name "${$json.title?.[0]}" --description "${($json['content:encoded']?.[0] || $json.description?.[0] || 'Auto-imported').replace(/"/g, '\\"')}" --url "${$json.link?.[0]}" --json`

// Format date for logging
new Date($json.pubDate?.[0]).toLocaleString('id-ID', { timeZone: 'Asia/Jakarta' })
```