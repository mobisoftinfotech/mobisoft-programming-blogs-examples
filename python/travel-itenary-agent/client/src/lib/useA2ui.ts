/**
 * Connects the A2UI MessageProcessor to React state.
 *
 * Protocol v1.0: the processor and basic catalog come from `@a2ui/web_core/v1_0`.
 * `@a2ui/react` 0.15 has no v1.0 entry point yet, so surfaces are drawn with its v0.9
 * <A2uiSurface>. Both catalogs share the same underlying components, and the client tests
 * check every surface the agent sends. Switch to `@a2ui/react/v1_0` once it ships.
 *
 * - The processor owns the UI state (surfaces, components, data model).
 * - We only track *which* surfaces exist; <A2uiSurface> re-renders itself
 *   when its components or data change.
 */
import {useCallback, useEffect, useRef, useState} from 'react';
import {
  MessageProcessor,
  basicCatalog,
  type ActionListener,
  type AgentToRendererMessage as A2uiMessage,
  type SurfaceModel,
} from '@a2ui/web_core/v1_0';
import type {ReactCatalogComponent} from '@a2ui/react/v0_9';

export function useA2ui(onAction: ActionListener) {
  // Keep the latest callback without re-creating the processor.
  const onActionRef = useRef(onAction);
  onActionRef.current = onAction;

  const [processor] = useState(
    () =>
      // basicCatalog's components are web components the React renderer can mount,
      // so we type the processor with the renderer's component type.
      new MessageProcessor<ReactCatalogComponent>([basicCatalog as never], action => onActionRef.current(action), {
        // Log renderer-side validation errors (Chapter 10 sends them back to the agent).
        errorHandler: error => console.warn('[A2UI]', error),
      }),
  );

  const [surfaces, setSurfaces] = useState<SurfaceModel<ReactCatalogComponent>[]>([]);

  useEffect(() => {
    const sync = () => setSurfaces(Array.from(processor.model.surfacesMap.values()));
    sync();
    const created = processor.onSurfaceCreated(sync);
    const deleted = processor.onSurfaceDeleted(sync);
    return () => {
      created.unsubscribe();
      deleted.unsubscribe();
    };
  }, [processor]);

  const process = useCallback((message: A2uiMessage) => processor.processMessages([message]), [processor]);

  return {surfaces, process};
}
