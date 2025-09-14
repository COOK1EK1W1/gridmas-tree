
"use client";
import { useRef, useState } from 'react';
import { syncStatusKeys, editorContext } from '@/util/context/editorContext';
import { Pattern } from '@prisma/client';
import { OnMount } from '@monaco-editor/react';

type Props = {
  children: React.ReactNode;
  cloudPattern: Pattern
};

// The provider for the pattern State
export default function CloudEditorProvider({ children, cloudPattern }: Props) {

  const [pattern, setPattern] = useState<string>(cloudPattern.data)

  const [lights, setLights] = useState<number[][]>([])

  const [syncStatus, setSyncStatus] = useState<typeof syncStatusKeys[number]>("idle")
  const codeRef = useRef<Parameters<OnMount>[0]>(null)


  return (
    <editorContext.Provider value={{
      pattern,
      patternID: cloudPattern.id,
      setPattern,
      lights,
      setLights,
      codeRef,
      syncStatus,
      setSyncStatus
    }} >
      {children}
    </ editorContext.Provider>
  );
}
