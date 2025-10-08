"use client";
import { OnMount } from '@monaco-editor/react';
import { Dispatch, RefObject, SetStateAction, createContext, useContext } from 'react';

export const syncStatusKeys = ["idle", "synced", "syncing", "notSynced", "error"] as const

export type RangeAttr = {
  name: string,
  default: number,
  min: number,
  max: number,
  step: number
}

export type ColorAttr = {
  name: string,
  default: string,
}

type provided = {
  attributeRefs: RefObject<any[]>,
  attributes: (RangeAttr | ColorAttr)[],
  setAttributes: Dispatch<SetStateAction<(RangeAttr | ColorAttr)[]>>,
  pattern: string,
  patternID: string | null,
  patternTitle: string | null,
  setPattern: Dispatch<SetStateAction<string>>,
  codeRef: RefObject<Parameters<OnMount>[0] | null>;
  syncStatus: typeof syncStatusKeys[number],
  setSyncStatus: Dispatch<SetStateAction<typeof syncStatusKeys[number]>>
}

export const editorContext = createContext<provided>(undefined as any);

/**
 * Adapter function to convert Python Store attribute data to TypeScript types
 * @param pyodideAttributeData Raw attribute data from Python Store
 * @returns Array of properly typed attributes
 */
export function adaptPythonAttributes(pyodideAttributeData: any[]): (RangeAttr | ColorAttr)[] {
  return pyodideAttributeData.map((attr: any) => {
    const name = attr[0];
    const value = attr[1];
    const type = attr[2]; // 'RangeAttr' or 'ColorAttr'
    
    if (type === 'RangeAttr' && attr.length >= 6) {
      return {
        name,
        default: value,
        min: attr[3],
        max: attr[4],
        step: attr[5] || 0.01
      } as RangeAttr;
    }
    
    // Otherwise, treat as ColorAttr
    return {
      name,
      default: value
    } as ColorAttr;
  });
}

export function useEditor() {
  const context = useContext(editorContext);

  if (context === undefined) {
    throw new Error('No waypoint context provided');
  }

  return context;
}
