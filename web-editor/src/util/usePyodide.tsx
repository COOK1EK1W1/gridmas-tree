// lib/usePyodide.ts
import { useEffect, useState } from "react";
import { PyodideInterface } from "pyodide";

export function usePyodide() {
  const [pyodide, setPyodide] = useState<PyodideInterface | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let isMounted = true;

    async function initPyodide() {
      const pyodideInstance = await (window as any).loadPyodide({
        indexURL: "https://cdn.jsdelivr.net/pyodide/v0.23.4/full/",
      });
      if (isMounted) {
        setPyodide(pyodideInstance);
        await pyodideInstance?.loadPackage("numpy")
        setLoading(false);
      }
    }

    initPyodide();

    return () => {
      isMounted = false;
    };
  }, []);

  return { pyodide, loading };
}

