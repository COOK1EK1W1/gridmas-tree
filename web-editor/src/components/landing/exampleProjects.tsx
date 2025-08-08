import Image from "next/image"
import Link from "next/link"

function Example({ title, image, link }: { title: string, image: string, link: string }) {
  return (
    <Link href={link}>
      <div className="rounded-xl overflow-hidden border border-red-200/40 bg-gradient-to-b from-white to-red-50/60 shadow-[0_10px_30px_-10px_rgba(220,38,38,0.35)] hover:shadow-[0_12px_40px_-8px_rgba(220,38,38,0.55)] transition">
        <Image width={210} height={500} src={image} alt="3dplasma tree" />
        <h4 className="text-center text-red-800 font-semibold py-1">{title}</h4>
      </div>
    </Link>
  )
}


export default function ExampleProjects() {
  return (
    <div className="text-black w-full rounded-3xl bg-white/70 backdrop-blur-[2px] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 p-4 gap-4">
      <div className="w-full"><Example title="3D Plasma" image="/3dplasma.jpeg" link="/p/3dplasma" /></div>
      <div className="w-full"><Example title="3D Fire" image="/3dfire.jpeg" link="/p/3dfire" /></div>
      <div className="w-full"><Example title="Caduceus" image="/caduceus.jpeg" link="/p/caduceus" /></div>
      <div className="w-full"><Example title="Borealis" image="/borealis.jpeg" link="/p/borealis" /></div>
      <div className="w-full"><Example title="Wave Flow" image="/waveflow.jpeg" link="/p/waveflow" /></div>
    </div>
  )
}
