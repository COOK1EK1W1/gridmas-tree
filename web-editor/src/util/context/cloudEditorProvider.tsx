
"use client";
import { useRef, useState } from 'react';
import { syncStatusKeys, editorContext, RangeAttr, ColorAttr } from '@/util/context/editorContext';
import { Pattern } from '@prisma/client';
import { OnMount } from '@monaco-editor/react';

type Props = {
  children: React.ReactNode;
  cloudPattern: Pattern
};

// The provider for the pattern State
export default function CloudEditorProvider({ children, cloudPattern }: Props) {

  const [pattern, setPattern] = useState<string>(cloudPattern.data)

  const [syncStatus, setSyncStatus] = useState<typeof syncStatusKeys[number]>("idle")
  const codeRef = useRef<Parameters<OnMount>[0]>(null)

  const attributeRefs = useRef([])

  const [attributes, setAttributes] = useState<(RangeAttr | ColorAttr)[]>([])

  return (
    <editorContext.Provider value={{
      attributeRefs,
      attributes,
      setAttributes,
      pattern,
      patternID: cloudPattern.id,
      patternTitle: cloudPattern.title,
      setPattern,
      codeRef,
      syncStatus,
      setSyncStatus
    }} >
      {children}
    </ editorContext.Provider>
  );
}
