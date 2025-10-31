import Link from "next/link";

export default function PrivacyPolicy() {
  return (
    <div className="bg-white max-w-4xl mx-auto px-4 py-8 h-full overflow-auto">
      <h1 className="text-3xl font-bold mb-6">Privacy Policy</h1>
      <p className="text-gray-600 mb-8">Last Updated: Oct 31, 2025</p>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Introduction</h2>
        <p className="mb-4">
          {`
          Welcome to GRIDmas tree ("we," "our," or "us"). We respect your privacy and are committed to protecting your personal information. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you visit our website https://gridmas-tree.vercel.app/ (the "Site") and use our services.`}
        </p>
        <p className="mb-4">
          Please read this Privacy Policy carefully. If you do not agree with the terms of this Privacy Policy, please do not access the Site. By using our services, you consent to the collection, use, and disclosure of your information as described in this Privacy Policy.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Information We Collect</h2>

        <h3 className="text-xl font-semibold mb-3">Personal Information</h3>
        <p className="mb-4">We may collect personal information that you voluntarily provide to us when you:</p>
        <ul className="list-disc pl-6 mb-4">
          <li>Create an account</li>
          <li>Use our pattern creation and management features</li>
          <li>Contact us with inquiries</li>
          <li>Respond to surveys</li>
          <li>Participate in promotions or contests</li>
        </ul>

        <p className="mb-4">The types of personal information we may collect include:</p>
        <ul className="list-disc pl-6 mb-4">
          <li>Name</li>
          <li>Email address</li>
          <li>Account credentials</li>
          <li>User ID</li>
          <li>Any other information you choose to provide</li>
        </ul>

        <h3 className="text-xl font-semibold mb-3">Usage Information</h3>
        <p className="mb-4">We automatically collect certain information when you visit, use, or navigate the Site. This information does not reveal your specific identity but may include:</p>
        <ul className="list-disc pl-6 mb-4">
          <li>Device and browser information</li>
          <li>IP address</li>
          <li>Usage patterns</li>
          <li>Referring webpage</li>
          <li>Geographic location</li>
          <li>System information</li>
        </ul>

        <h3 className="text-xl font-semibold mb-3">Pattern Data</h3>
        <p className="mb-4">When you create, edit, or share pattersn, we collect and store:</p>
        <ul className="list-disc pl-6 mb-4">
          <li>Pattern titles</li>
          <li>Pattern content and configurations</li>
          <li>Other pattern-related metadata</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">How We Use Your Information</h2>
        <p className="mb-4">We may use the information we collect for various purposes, including:</p>
        <ul className="list-disc pl-6 mb-4">
          <li>Providing, maintaining, and improving our services</li>
          <li>Processing your account registration</li>
          <li>Fulfilling your requests for pattern creation and management</li>
          <li>Responding to your inquiries</li>
          <li>Sending administrative information</li>
          <li>Sending marketing communications (with your consent)</li>
          <li>Personalizing your experience</li>
          <li>Monitoring and analyzing usage trends</li>
          <li>Detecting, preventing, and addressing technical issues</li>
          <li>Enforcing our Terms of Service</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Data Retention</h2>
        <p className="mb-4">
          We retain your personal information only for as long as necessary to fulfill the purposes outlined in this Privacy Policy, unless a longer retention period is required or permitted by law.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Data Security</h2>
        <p className="mb-4">
          We implement appropriate technical and organizational measures to protect the security of your personal information. However, please be aware that no method of transmission over the Internet or electronic storage is 100% secure, and we cannot guarantee absolute security.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Third-Party Services</h2>
        <p className="mb-4">
          Our Site may contain links to third-party websites or services that are not owned or controlled by us. We have no control over and assume no responsibility for the content, privacy policies, or practices of any third-party sites or services.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">User Rights</h2>
        <p className="mb-4">Depending on your location, you may have certain rights regarding your personal information, including:</p>
        <ul className="list-disc pl-6 mb-4">
          <li>Right to access the personal information we have about you</li>
          <li>Right to request correction of inaccurate information</li>
          <li>Right to request deletion of your information</li>
          <li>Right to object to or restrict certain processing</li>
          <li>Right to data portability</li>
        </ul>
        <p className="mb-4">To exercise these rights, please contact us using the information provided below.</p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">{`Children's Privacy`}</h2>
        <p className="mb-4">
          Our services are not intended for individuals under the age of 13. We do not knowingly collect personal information from children under 13.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">International Data Transfers</h2>
        <p className="mb-4">
          Your information may be transferred to and processed in countries other than your country of residence. These countries may have different data protection laws than your country.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Changes to This Privacy Policy</h2>
        <p className="mb-4">
          {`We may update this Privacy Policy from time to time. The updated version will be indicated by an updated "Last Updated" date. We encourage you to review this Privacy Policy periodically.`}
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Contact Us</h2>
        <p className="mb-4">
          If you have any questions or concerns about this Privacy Policy, please contact us at:
          <br />
          Email: <Link href="mailto:ciarancook1@gmail.com" className="text-blue-600 hover:underline">ciarancook1@gmail.com</Link>
        </p>
      </section>

      <p className="text-gray-600">
        By using our Site, you acknowledge that you have read and understood this Privacy Policy.
      </p>
    </div>
  );
}
