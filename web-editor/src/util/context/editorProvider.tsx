"use client";
import { useRef, useState } from 'react';
import { syncStatusKeys, editorContext } from '@/util/context/editorContext';
import { OnMount } from '@monaco-editor/react';

type Props = {
  children: React.ReactNode;
};

// The provider for the pattern State
export default function EditorProvider({ children }: Props) {

  const [pattern, setPattern] = useState<string>("")

  const [syncStatus, setSyncStatus] = useState<typeof syncStatusKeys[number]>("idle")
  const codeRef = useRef<Parameters<OnMount>[0] | null>(null)

  return (
    <editorContext.Provider value={{
      patternID: null,
      patternTitle: null,
      pattern,
      setPattern,
      codeRef,
      syncStatus,
      setSyncStatus
    }} >
      {children}
    </ editorContext.Provider>
  );
}
