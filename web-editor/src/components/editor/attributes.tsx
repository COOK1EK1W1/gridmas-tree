import { useEditor } from "@/util/context/editorContext";
import { Slider } from "../ui/slider";
import { useEffect, useState } from "react";

export default function Attributes() {

  const { attributes, attributeRefs } = useEditor()
  const [currentValues, setCurrentValues] = useState<(number | string)[]>([])

  const isRangeAttr = (attr: any): attr is { name: string; default: number; min: number; max: number; step: number } => {
    return 'min' in attr && 'max' in attr && 'step' in attr;
  };

  // Initialize current values when attributes change
  useEffect(() => {
    if (attributes) {
      const initialValues = attributes.map(attr =>
        isRangeAttr(attr) ? attr.default : attr.default
      )
      setCurrentValues(initialValues)
    }
  }, [attributes])

  // Ensure the refs array is the right length and store current values
  useEffect(() => {
    if (attributeRefs.current && attributes) {
      attributeRefs.current = attributeRefs.current.slice(0, attributes.length)

      // Store current values in refs for easy access
      for (let i = 0; i < attributes.length; i++) {
        if (attributeRefs.current[i]) {
          attributeRefs.current[i].currentValue = currentValues[i]
        }
      }
    }
  }, [attributes?.length, currentValues])

  return (
    <div className="md:w-1/2 h-40 md:h-52">
      {attributes.length > 0 ? (<div className="overflow-auto w-full candy-frame h-full bg-white rounded grid grid-cols-1 lg:grid-cols-2 xxl:grid-cols-3 gap-8">
        {attributes.map((attr, i) => (
          <div key={i}>
            <div className="pb-2">{attr.name}</div>
            {isRangeAttr(attr) ? (
              <Slider
                ref={(el) => {
                  if (attributeRefs.current) {
                    attributeRefs.current[i] = el
                  }
                }}
                value={currentValues[i] !== undefined ? [currentValues[i] as number] : [attr.default]}
                onValueChange={(values) => {
                  const newValues = [...currentValues]
                  newValues[i] = values[0]
                  setCurrentValues(newValues)
                }}
                max={attr.max}
                min={attr.min}
                step={attr.step}
              />
            ) : (
              <div className="flex items-center gap-2">
                <input
                  ref={(el) => {
                    if (attributeRefs.current) {
                      attributeRefs.current[i] = el
                    }
                  }}
                  type="color"
                  value={currentValues[i] !== undefined ? currentValues[i] as string : attr.default}
                  onChange={(e) => {
                    const newValues = [...currentValues]
                    newValues[i] = e.target.value
                    setCurrentValues(newValues)
                  }}
                  className="w-8 h-8 rounded border"
                />
                <span className="text-sm text-gray-600">{currentValues[i] !== undefined ? currentValues[i] : attr.default}</span>
              </div>
            )}
          </div>
        ))}
      </div>) : <div className="flex w-full flex-col justify-center items-center w-full candy-frame h-full bg-white rounded">
        <div>
          Attributes allow you to change parameters while the pattern is running.
        </div>
        <code>{`variable = RangeAttr("myVariable", 0, -1, 1, 0.01)`}</code>
      </div>
      }
    </div >
  )

}
