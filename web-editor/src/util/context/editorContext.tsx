"use client";
import { OnMount } from '@monaco-editor/react';
import { Dispatch, RefObject, SetStateAction, createContext, useContext } from 'react';

export const syncStatusKeys = ["idle", "synced", "syncing", "notSynced", "error"] as const

type provided = {
  pattern: string,
  patternID: string | null,
  patternTitle: string | null,
  setPattern: Dispatch<SetStateAction<string>>,
  codeRef: RefObject<Parameters<OnMount>[0] | null>;
  syncStatus: typeof syncStatusKeys[number],
  setSyncStatus: Dispatch<SetStateAction<typeof syncStatusKeys[number]>>
}

export const editorContext = createContext<provided>(undefined as any);

export function useEditor() {
  const context = useContext(editorContext);

  if (context === undefined) {
    throw new Error('No waypoint context provided');
  }

  return context;
}
