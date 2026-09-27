# RSS/Atom Feed Field Mapping Patterns

## Standard RSS 2.0 Structure

```xml
<rss version="2.0">
  <channel>
    <title>Site Title</title>
    <link>https://example.com</link>
    <description>Site description</description>
    <item>
      <title>Post Title</title>
      <link>https://example.com/post</link>
      <description>Short excerpt</description>
      <content:encoded><![CDATA[Full HTML content]]></content:encoded>
      <pubDate>Mon, 01 Jan 2026 08:00:00 +0000</pubDate>
      <guid isPermaLink="true">https://example.com/post</guid>
      <category>Category Name</category>
      <author>author@example.com (Author Name)</author>
    </item>
  </channel>
</rss>
```

## Parsed JSON Output (n8n XML Node)

```json
{
  "rss": {
    "channel": {
      "title": ["Site Title"],
      "link": ["https://example.com"],
      "description": ["Site description"],
      "item": [
        {
          "title": ["Post Title"],
          "link": ["https://example.com/post"],
          "description": ["Short excerpt"],
          "content:encoded": ["Full HTML content"],
          "pubDate": ["Mon, 01 Jan 2026 08:00:00 +0000"],
          "guid": [{"_": "https://example.com/post", "isPermaLink": "true"}],
          "category": ["Category Name"],
          "author": ["author@example.com (Author Name)"]
        }
      ]
    }
  }
}
```

## Field Access Patterns in n8n

| Source Field | n8n Expression | Notes |
|--------------|----------------|-------|
| Title | `{{$json.title[0]}}` or `{{$json.title}}` | Arrays auto-stringify |
| Link | `{{$json.link[0]}}` | |
| Description | `{{$json.description[0]}}` | Short excerpt |
| Full Content | `{{$json['content:encoded'][0]}}` | **Use bracket notation for colon** |
| PubDate | `{{$json.pubDate[0]}}` | Parse with `new Date()` |
| GUID | `{{$json.guid[0]._}}` | Unique ID |
| Category | `{{$json.category[0]}}` | May be array |
| Author | `{{$json.author[0]}}` | Email + name |

## Common Feed Variations

### WordPress RSS (with content:encoded)
```json
{
  "title": ["Post Title"],
  "link": ["https://site.com/post/"],
  "description": ["Excerpt..."],
  "content:encoded": ["<p>Full HTML content with images</p>"],
  "pubDate": ["Wed, 15 Jan 2026 10:30:00 +0000"],
  "guid": [{"_": "https://site.com/?p=123", "isPermaLink": "false"}],
  "category": ["Tutorial", "WordPress"],
  "creator": ["admin"],
  "comments": ["https://site.com/post/#comments"]
}
```

### Atom 1.0
```json
{
  "feed": {
    "entry": [{
      "title": [{"_": "Post Title", "type": "html"}],
      "link": [{"href": "https://site.com/post/", "rel": "alternate"}],
      "summary": [{"_": "Excerpt...", "type": "html"}],
      "content": [{"_": "<p>Full content</p>", "type": "html"}],
      "published": ["2026-01-15T10:30:00Z"],
      "updated": ["2026-01-15T10:30:00Z"],
      "id": ["https://site.com/post/"],
      "author": [{"name": ["Author Name"], "email": ["author@site.com"]}]
    }]
  }
}
```

## n8n XML Node Config for Common Feeds

### Standard RSS
```json
{
  "fieldToSplit": "rss.channel.item"
}
```

### WordPress (includes content:encoded)
```json
{
  "fieldToSplit": "rss.channel.item"
}
```

### Atom
```json
{
  "fieldToSplit": "feed.entry"
}
```

## Date Parsing in n8n Expressions

```javascript
// Convert pubDate to ISO string
new Date($json.pubDate[0]).toISOString()

// Format as YYYY-MM-DD
$now.format('YYYY-MM-DD')

// Compare dates (is item newer than last run?)
new Date($json.pubDate[0]) > new Date($getWorkflowStaticData('global').lastRun || 0)
```

## Content Extraction Tips

| Goal | Approach |
|------|----------|
| Plain text from HTML | Use `{{$json['content:encoded'][0].replace(/<[^>]*>/g, '').substring(0, 500)}}` |
| First image URL | `{{$json['content:encoded'][0].match(/<img[^>]+src=["']([^"']+)["']/)?.[1]}}` |
| Remove scripts/styles | Replace `/<script[^>]*>.*?<\/script>/gi` and `/<style[^>]*>.*?<\/style>/gi` |
| Truncate at word boundary | `.substring(0, 500).replace(/\s+\S*$/, '') + '...'` |

## Handling Missing Fields (Defensive Expressions)

```javascript
// Coalesce multiple possible fields
$json.title?.[0] || $json['dc:title']?.[0] || 'Untitled'

$json['content:encoded']?.[0] || $json.description?.[0] || $json.summary?.[0] || ''

$json.link?.[0] || $json.guid?.[0]?._ || $json.id?.[0] || ''
```

## Deduplication Keys

| Feed Type | Best Key |
|-----------|----------|
| Standard RSS | `guid._` or `link` |
| WordPress | `guid._` (contains `?p=ID`) |
| Atom | `id` |
| Custom | `link` + `pubDate` hash |