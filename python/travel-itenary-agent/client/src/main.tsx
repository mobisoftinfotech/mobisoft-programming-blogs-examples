import {StrictMode} from 'react';
import {createRoot} from 'react-dom/client';
import {injectBasicCatalogStyles, setMarkdownRenderer} from '@a2ui/web_core/v1_0';
import {renderMarkdown} from '@a2ui/markdown-it';
import App from './App';
import './styles.css';

// Default styles for the basic catalog components (Text, Button, TextField…).
injectBasicCatalogStyles();
// A2UI v1.0 has no heading variants: Text content is Markdown ("## Where to next?").
// The official renderer uses markdown-it and sanitises the HTML with DOMPurify.
setMarkdownRenderer(renderMarkdown);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
