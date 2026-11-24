/**
 * Cross-language contract test for every surface the agent can send.
 * The Python builders' golden output must pass the official A2UI v1.0
 * MessageProcessor without errors, and must render with the React renderer.
 */
import {describe, expect, it} from 'vitest';
import {fireEvent, render, waitFor} from '@testing-library/react';
import {MessageProcessor, basicCatalog as v1Catalog, setMarkdownRenderer, type AgentToRendererMessage as A2uiMessage} from '@a2ui/web_core/v1_0';
import {renderMarkdown} from '@a2ui/markdown-it';
const basicCatalog = v1Catalog as never;
import {A2uiSurface, type ReactCatalogComponent} from '@a2ui/react/v0_9';
import welcome from '../../../agent/tests/golden/welcome.json';
import itinerary from '../../../agent/tests/golden/itinerary.json';
import hotels from '../../../agent/tests/golden/hotels.json';
import bookingForm from '../../../agent/tests/golden/booking_form.json';
import bookingConfirmed from '../../../agent/tests/golden/booking_confirmed.json';
import notice from '../../../agent/tests/golden/notice.json';

// v1.0 headings are Markdown; install the official renderer like main.tsx does.
setMarkdownRenderer(renderMarkdown);

const cases: [string, string, unknown[]][] = [
  ['welcome', 'welcome', welcome],
  ['itinerary', 'itinerary', itinerary],
  ['hotels', 'hotels', hotels],
  ['booking form', 'booking', bookingForm],
  ['out-of-scope notice', 'notice', notice],
];

function mount(messages: unknown[], surfaceId: string) {
  const actions: {name: string; context: Record<string, unknown>}[] = [];
  const processor = new MessageProcessor<ReactCatalogComponent>([basicCatalog], a => {
    actions.push(a as never);
  });
  const errors = processor.processMessagesWithErrors(messages as A2uiMessage[]);
  const surface = processor.getSurface(surfaceId)!;
  const view = render(<A2uiSurface surface={surface} />);
  return {processor, errors, view, actions};
}

// The basic catalog renders Lit web components, which update asynchronously.
const textOf = (el: HTMLElement) => (el.textContent ?? '').replace(/\s+/g, ' ');
const buttons = (el: HTMLElement, label: string) =>
  Array.from(el.querySelectorAll('button')).filter(b => textOf(b).includes(label));

describe('golden surfaces from the Python agent', () => {
  it.each(cases)('%s is valid A2UI v1.0 and renders', (_name, id, messages) => {
    const {errors, view} = mount(messages, id);
    expect(errors).toEqual([]);
    expect(view.container.innerHTML.length).toBeGreaterThan(0);
  });

  it('itinerary: nested templates render every day and activity', async () => {
    const {view} = mount(itinerary, 'itinerary');
    await waitFor(() => expect(textOf(view.container)).toContain('Day 3'));
    const text = textOf(view.container);
    expect(text).toContain('Thailand: Temples, Mountains & Islands');
    expect(text).toContain('Day 3');
    expect(text).toContain('Grand Palace & Wat Pho'); // day 2 → activity 1
    expect(text).toContain('Chiang Mai · 2 nights'); // stops template
    expect(text).toContain('Dress modestly'); // tips template
  });

  it('v1.0 headings render as real headings through the Markdown renderer', async () => {
    const {view} = mount(welcome, 'welcome');
    await waitFor(() => expect(view.container.querySelector('h2')?.textContent).toContain('Where to next?'));
    expect(textOf(view.container)).not.toContain('## ');
  });

  it('itinerary: a refinement is data-only', async () => {
    const {processor, view} = mount(itinerary, 'itinerary');
    const errors = processor.processMessagesWithErrors([
      {version: '1.0', updateDataModel: {surfaceId: 'itinerary', path: '/itinerary/title', value: 'Thailand, slowly'}},
    ] as A2uiMessage[]);
    expect(errors).toEqual([]);
    await waitFor(() => expect(textOf(view.container)).toContain('Thailand, slowly'));
  });

  it('hotels: the Select button in each templated card sends that card\'s hotel id', async () => {
    const {view, actions} = mount(hotels, 'hotels');
    await waitFor(() => expect(buttons(view.container, 'Select')).toHaveLength(4));
    fireEvent.click(buttons(view.container, 'Select')[2]);
    const items = (hotels[2] as {updateDataModel: {value: {items: {id: string}[]}}}).updateDataModel.value.items;
    await waitFor(() => expect(actions.at(-1)).toMatchObject({name: 'select_hotel', context: {hotelId: items[2].id}}));
  });

  it('welcome: a suggestion button sends its own prompt', async () => {
    const {view, actions} = mount(welcome, 'welcome');
    await waitFor(() => expect(buttons(view.container, 'Thailand')).toHaveLength(1));
    fireEvent.click(buttons(view.container, 'Thailand')[0]);
    await waitFor(() =>
      expect(actions.at(-1)).toMatchObject({name: 'suggest', context: {prompt: expect.stringContaining('Thailand')}}),
    );
  });

  it('notice: explains the scope and offers a tailored travel suggestion', async () => {
    const {view, actions} = mount(notice, 'notice');
    await waitFor(() => expect(textOf(view.container)).toContain("That's outside my travel desk"));
    expect(textOf(view.container)).toContain('You asked about: fixing Python code');
    fireEvent.click(buttons(view.container, 'San Francisco')[0]);
    await waitFor(() =>
      expect(actions.at(-1)).toMatchObject({name: 'suggest', context: {prompt: 'Plan a 3-day tech trip to San Francisco'}}),
    );
  });

  it('booking: the confirmation replaces the view on the same surface and closes the hotel list', () => {
    const processor = new MessageProcessor([basicCatalog]);
    expect(processor.processMessagesWithErrors([...hotels, ...bookingForm] as A2uiMessage[])).toEqual([]);
    const after = (bookingConfirmed as {createSurface?: unknown}[]).filter(m => !m.createSurface); // surface already open
    expect(processor.processMessagesWithErrors(after as A2uiMessage[])).toEqual([]);
    expect(processor.getSurface('hotels')).toBeUndefined();
    expect(processor.getSurface('booking')!.dataModel.get('/confirmation/reference')).toMatch(/^WND-/);
  });
});
