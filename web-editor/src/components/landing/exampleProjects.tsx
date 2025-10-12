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

const others = [
  { url: '/p/1b309b03-693e-4b4d-ae33-7b6cb2401af0', title: 'Checkers' },
  { url: '/p/83243776-1c2f-4997-8c4b-75deb987eefd', title: 'Waves' },
  { url: '/p/70369885-5cb1-488c-a537-4e8cb82a82fc', title: 'XYZ Planes' },
  { url: '/p/ea5ed82f-7a4b-4bf0-b71b-7492876da96c', title: 'RGB Helix' },
  { url: '/p/349866b2-92a1-417f-ad00-cc2ce1de3b38', title: 'XYZ Planes Original' },
  { url: '/p/5c90eeaf-a629-4e68-ab73-657a29f41446', title: 'Center Finder' },
  { url: '/p/76b5d311-35c2-40e4-aad3-6488fc3003ff', title: 'Fade Waves' },
  { url: '/p/de8d9b57-6e98-430e-9e03-9dc4d744a701', title: 'Color Switcher' },
  { url: '/p/94db3cf6-ab44-4e05-9429-9e420954c4f0', title: 'Starry Night' },
  { url: '/p/11bc5f73-6a56-4cf9-9125-5409c53d8b74', title: 'Murica' },
  { url: '/p/0fdec731-b32b-4458-a941-83cb66f95571', title: 'Planes' },
  { url: '/p/187aae72-8b37-408e-acd7-fa8a74110189', title: 'Lerpy' },
  { url: '/p/86536367-39b0-4784-bdf7-fc65782b1f2e', title: 'Fountain' },
  { url: '/p/233c3162-a3e6-4ea0-b7da-7e73f6da2179', title: 'Hue Rotate' },
  { url: '/p/e3cfa89b-8058-41b0-8f72-c9a1057dc7fa', title: 'Jumpy Balls' },
  { url: '/p/b1f0bd8b-65c5-439d-a522-47be8f98fd40', title: 'Rippling Waves' },
  { url: '/p/6312f79a-06b9-411a-a464-cdcd2266b83c', title: 'Sphere Fill' },
  { url: '/p/cb7ccf50-2ae5-4fb3-a6ce-79ee7af4e2c5', title: 'Snowing' },
  { url: '/p/11cb6147-7b2c-474f-a209-ee59072774e0', title: 'Solid Color' },
  { url: '/p/f9950e22-5004-4976-a7fc-05c67169952c', title: 'Twinkle' },
  { url: '/p/eb341f91-bb0f-4f95-839a-827e201bb706', title: 'Twinkling Stars' },
  { url: '/p/976a2178-10ba-411d-a8a2-70da85d06b67', title: 'RGB' },
  { url: '/p/447bd88a-e747-4449-bbde-143d5d056cb1', title: 'Fireworks' },
  { url: '/p/67dafedd-d7a1-438b-bea0-c017b3ef9eae', title: 'Helix Spin' },
  { url: '/p/1387fd1e-7936-4d43-88fc-0961049255c3', title: 'RGB Spheres' }
]

export default function ExampleProjects() {
  return (
    <div className="text-black w-full rounded-3xl bg-white/70 backdrop-blur-[2px] grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 p-4 gap-4">
      <div className="w-full"><Example title="3D Plasma" image="/3dplasma.jpeg" link="/p/3dplasma" /></div>
      <div className="w-full"><Example title="3D Fire" image="/3dfire.jpeg" link="/p/3dfire" /></div>
      <div className="w-full"><Example title="Caduceus" image="/caduceus.jpeg" link="/p/caduceus" /></div>
      <div className="w-full"><Example title="Borealis" image="/borealis.jpeg" link="/p/borealis" /></div>
      <div className="w-full"><Example title="Wave Flow" image="/waveflow.jpeg" link="/p/waveflow" /></div>
      <div className="w-full"><Example title="Strip" image="/strip.jpeg" link="/p/strip" /></div>
      <div className="w-full"><Example title="Spin" image="/spin.jpeg" link="/p/spin" /></div>
      <div className="w-full"><Example title="Wandering Ball" image="/wanderingball.jpeg" link="/p/wanderingball" /></div>
      {others.map((x, i) => (
        < div key={i} className="relative w-[210px]" >
          <div className="w-full h-20 rounded-xl overflow-hidden border border-red-200/40 bg-gradient-to-b from-white to-red-50/60 shadow-[0_10px_30px_-10px_rgba(220,38,38,0.35)] hover:shadow-[0_12px_40px_-8px_rgba(220,38,38,0.55)] transition">
            <Link href={x.url} className="h-full p-2 text-red-800 flex flex-col items-center justify-around">
              <h4 className="text-center font-semibold text-sm leading-tight">{x.title}</h4>
            </Link>
          </div>
        </div >
      ))}

    </div>
  )
}
