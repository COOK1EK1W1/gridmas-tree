import Link from "next/link";

export default function Terms() {
  return (
    <div className="bg-white max-w-4xl mx-auto px-4 py-8 h-full overflow-auto">
      <h1 className="text-3xl font-bold mb-6">Terms of Service</h1>
      <p className="text-gray-600 mb-8">Last Updated: Oct 31, 2025</p>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Introduction</h2>
        <p className="mb-4">
          {`Welcome to GRIDmas Tree. These Terms of Service ("Terms") govern your access to and use of the GRIDmas Tree website and services available at https://gridmas-tree.vercel.app/ (collectively, the "Service").`}
        </p>
        <p className="mb-4">
          By accessing or using the Service, you agree to be bound by these Terms. If you disagree with any part of the Terms, you may not access the Service.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">User Accounts</h2>

        <h3 className="text-xl font-semibold mb-3">Registration</h3>
        <p className="mb-4">
          To access certain features of the Service, you must register for an account. When you register, you must provide accurate and complete information and keep this information updated.
        </p>

        <h3 className="text-xl font-semibold mb-3">Account Security</h3>
        <p className="mb-4">
          You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account. You agree to notify us immediately of any unauthorized use of your account.
        </p>

        <h3 className="text-xl font-semibold mb-3">User Limitations</h3>
        <p className="mb-4">
          We may impose limits on the number of patterns you can create based on your account type. As indicated in our system configuration, there may be a maximum number of patterns per user. Once you reach this limit, you will not be able to create additional patterns until you delete existing ones or upgrade your account (if applicable).
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">User Content</h2>

        <h3 className="text-xl font-semibold mb-3">Pattern Data</h3>
        <p className="mb-4">
          When you create patterns through our Service, you retain ownership of your content. However, by creating and storing pattern data on our platform, you grant us a non-exclusive, worldwide, royalty-free license to use, reproduce, modify, adapt, publish, and display such content solely for the purpose of providing and improving the Service.
        </p>

        <h3 className="text-xl font-semibold mb-3">Public Patterns</h3>
        <p className="mb-4">
          By creating a pattern, it is public by default, you understand and agree that they may be accessible to other users of the Service. You are solely responsible for the patterns you create and share.
        </p>

        <h3 className="text-xl font-semibold mb-3">Prohibited Content</h3>
        <p className="mb-4">You agree not to create or share patterns that:</p>
        <ul className="list-disc pl-6 mb-4">
          <li>Violate any applicable laws or regulations</li>
          <li>Infringe on the intellectual property rights of others</li>
          <li>Contain malicious code or links</li>
          <li>Contain offensive, harmful, or inappropriate content</li>
          <li>Could be used for illegal activities or to harass others</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Service Limitations and Modifications</h2>

        <h3 className="text-xl font-semibold mb-3">Service Availability</h3>
        <p className="mb-4">
          We strive to ensure that the Service is available at all times, but we do not guarantee uninterrupted access. We reserve the right to suspend or restrict access to some features to users without prior notice.
        </p>

        <h3 className="text-xl font-semibold mb-3">Service Modifications</h3>
        <p className="mb-4">
          We reserve the right, at our sole discretion, to modify or replace these Terms at any time. We will provide notice of any significant changes by posting the updated Terms on the Service. Your continued use of the Service after such modifications constitutes your acceptance of the new Terms.
        </p>

        <h3 className="text-xl font-semibold mb-3">Pattern Storage and Deletion</h3>
        <p className="mb-4">
          We reserve the right to delete inactive patterns or accounts after an extended period of inactivity. We will attempt to notify you before such deletion occurs.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Intellectual Property</h2>

        <h3 className="text-xl font-semibold mb-3">Our Content</h3>
        <p className="mb-4">
          The Service and its original content (excluding user-created patterns), features, and functionality are and will remain the exclusive property of GRIDmas tree and its licensors. The Service is protected by copyright, trademark, and other laws.
        </p>

        <h3 className="text-xl font-semibold mb-3">Feedback</h3>
        <p className="mb-4">
          If you provide us with any feedback or suggestions regarding the Service, you assign to us all rights in such feedback and agree that we shall have the right to use such feedback in any manner we deem appropriate.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Disclaimers</h2>

        <h3 className="text-xl font-semibold mb-3">{`"As Is" and "As Available"`}</h3>
        <p className="mb-4">
          {`The Service is provided on an "AS IS" and "AS AVAILABLE" basis. We expressly disclaim all warranties of any kind, whether express or implied, including but not limited to the implied warranties of merchantability, fitness for a particular purpose, and non-infringement.`}
        </p>

        <h3 className="text-xl font-semibold mb-3">No Guarantee</h3>
        <p className="mb-4">
          We make no warranty that the Service will meet your requirements, be available on an uninterrupted, secure, or error-free basis, or that defects will be corrected.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Limitation of Liability</h2>
        <p className="mb-4">
          In no event shall GRIDmas Tree, its directors, employees, partners, agents, suppliers, or affiliates be liable for any indirect, incidental, special, consequential, or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from:
        </p>
        <ul className="list-disc pl-6 mb-4">
          <li>Your access to or use of or inability to access or use the Service</li>
          <li>Any conduct or content of any third party on the Service</li>
          <li>Any content obtained from the Service</li>
          <li>Unauthorized access, use, or alteration of your transmissions or content</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Indemnification</h2>
        <p className="mb-4">
          {`You agree to defend, indemnify, and hold harmless GRIDmas Tree and its licensees, licensors, employees, contractors, agents, officers, and directors from and against any and all claims, damages, obligations, losses, liabilities, costs, or debt, and expenses (including but not limited to attorney's fees), resulting from or arising out of:`}
        </p>
        <ul className="list-disc pl-6 mb-4">
          <li>Your use and access of the Service</li>
          <li>Your violation of any term of these Terms</li>
          <li>Your violation of any third-party right, including without limitation any copyright, property, or privacy right</li>
        </ul>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Governing Law</h2>
        <p className="mb-4">
          These Terms shall be governed and construed in accordance with the laws of Scotland, without regard to its conflict of law provisions.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Dispute Resolution</h2>
        <p className="mb-4">
          Any disputes arising out of or relating to these Terms or the Service shall be resolved through binding arbitration in accordance with the rules of the Scottish Arbitration Centre in Edinburgh, Scotland.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Severability</h2>
        <p className="mb-4">
          If any provision of these Terms is held to be unenforceable or invalid, such provision will be changed and interpreted to accomplish the objectives of such provision to the greatest extent possible under applicable law, and the remaining provisions will continue in full force and effect.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Entire Agreement</h2>
        <p className="mb-4">
          These Terms constitute the entire agreement between you and GRIDmas Tree regarding the Service and supersede all prior agreements and understandings, whether written or oral.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-2xl font-semibold mb-4">Contact Information</h2>
        <p className="mb-4">
          If you have any questions about these Terms, please contact us at:
          <br />
          Email: <Link href="mailto:ciarancook1@gmail.com" className="text-blue-600 hover:underline">ciarancook1@gmail.com</Link>
        </p>
      </section>

      <p className="text-gray-600">
        By using our Service, you acknowledge that you have read and understood these Terms of Service.
      </p>
    </div>
  );
}

