import DOMPurify from 'dompurify';
import { marked } from 'marked';

// Links in notes open in a new tab and can't reach back into the app.
DOMPurify.addHook('afterSanitizeAttributes', (node) => {
	if (node.tagName === 'A') {
		node.setAttribute('target', '_blank');
		node.setAttribute('rel', 'noopener noreferrer');
	}
});

/** Markdown to sanitized HTML, safe for {@html}. */
export function renderMarkdown(source: string): string {
	const html = marked.parse(source, { async: false, gfm: true, breaks: true });
	return DOMPurify.sanitize(html, { USE_PROFILES: { html: true } });
}

/**
 * Plain-text excerpt of markdown, e.g. for cards. DOMParser builds an inert
 * document, so nothing in the note (like images) loads while we read its text.
 */
export function markdownExcerpt(source: string, length = 180): string {
	const doc = new DOMParser().parseFromString(renderMarkdown(source), 'text/html');
	// Keep a visible break between headings, paragraphs and list items.
	for (const block of doc.body.querySelectorAll('h1, h2, h3, h4, h5, h6, p, li, blockquote, pre')) {
		block.append(' · ');
	}
	const text = (doc.body.textContent ?? '')
		.replace(/\s+/g, ' ')
		.replace(/(\s·)+/g, ' ·')
		.replace(/[\s·]+$/, '')
		.trim();
	return text.length > length ? `${text.slice(0, length).trimEnd()}…` : text;
}
