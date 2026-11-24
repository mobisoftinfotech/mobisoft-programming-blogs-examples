/**
 * Cross-language contract test: the Python builder's golden output
 * (agent/tests/golden/trip_form.json) must pass the official A2UI v1.0
 * MessageProcessor without errors, and must render.
 */
import {describe, expect, it} from 'vitest';
import {render} from '@testing-library/react';
import {MessageProcessor, basicCatalog as v1Catalog} from '@a2ui/web_core/v1_0';
const basicCatalog = v1Catalog as never;
import {A2uiSurface, type ReactCatalogComponent} from '@a2ui/react/v0_9';
import golden from '../../../agent/tests/golden/trip_form.json';

describe('trip form (golden from the Python agent)', () => {
  it('is valid A2UI v1.0', () => {
    const processor = new MessageProcessor([basicCatalog]);
    const errors = processor.processMessagesWithErrors(golden);
    expect(errors).toEqual([]);
    expect(processor.getSurface('trip_form')).toBeDefined();
  });

  it('renders the surface', () => {
    const processor = new MessageProcessor<ReactCatalogComponent>([basicCatalog]);
    processor.processMessages(golden as never);
    const surface = processor.getSurface('trip_form')!;
    const {container} = render(<A2uiSurface surface={surface} />);
    expect(container.innerHTML.length).toBeGreaterThan(0);
  });

  it('accepts an update to an existing surface (Chapter 4: agent pre-fills the form)', () => {
    const processor = new MessageProcessor([basicCatalog]);
    processor.processMessages(golden as never);
    // The server skips createSurface when the surface is already open.
    const updateOnly = [
      golden[1], // updateComponents (same layout)
      {version: '1.0', updateDataModel: {surfaceId: 'trip_form', path: '/trip/destination', value: 'Lisbon'}},
    ];
    expect(processor.processMessagesWithErrors(updateOnly)).toEqual([]);
    expect(processor.getSurface('trip_form')!.dataModel.get('/trip/destination')).toBe('Lisbon');
  });

  it('rejects creating the same surface twice (why the server tracks open surfaces)', () => {
    const processor = new MessageProcessor([basicCatalog]);
    processor.processMessages(golden as never);
    const errors = processor.processMessagesWithErrors([golden[0]]);
    expect(JSON.stringify(errors)).toContain('already exists');
  });
});
