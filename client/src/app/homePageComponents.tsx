import Link from "next/link";

const Header = () => {
  return (
    <header className="bg-white/80 backdrop-blur-md shadow-sm fixed w-full z-50 transition-all duration-300 hover:shadow-md">
      <div className="container mx-auto px-6 py-4">
        <div className="flex justify-between items-center">
          <Link href="/" className="flex items-center space-x-2">
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
              EduTECH
            </span>
          </Link>
          <nav className="hidden md:flex items-center space-x-8">
            <Link
              href="#features"
              className="text-gray-700 hover:text-indigo-600 font-medium transition-colors"
            >
              Features
            </Link>
            <Link
              href="#about"
              className="text-gray-700 hover:text-indigo-600 font-medium transition-colors"
            >
              About
            </Link>
            <Link
              href="#contact"
              className="text-gray-700 hover:text-indigo-600 font-medium transition-colors"
            >
              Contact
            </Link>
            <Link
              href="/register"
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-5 py-2 rounded-full font-medium hover:shadow-lg hover:shadow-blue-100 transition-all"
            >
              Get Started
            </Link>
          </nav>
          <button className="md:hidden text-gray-700">
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16m-7 6h7"
              />
            </svg>
          </button>
        </div>
      </div>
    </header>
  );
};

const HeroSection = () => {
  return (
    <section className="relative min-h-[60vh] flex items-center pt-20 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-br from-blue-50 to-indigo-50 -z-10"></div>
      <div className="absolute top-0 right-0 w-1/2 h-full bg-gradient-to-l from-blue-100 to-transparent -z-10"></div>

      <div className="container mx-auto px-6 py-20">
        <div className="flex gap-6 flex-col lg:flex-row items-center justify-center">
          <div className="lg:w-1/2 xl:w-1/3 p-8 bg-white/90 rounded-lg shadow-lg">
            <h1 className="text-4xl font-bold text-gray-900 mb-4">
              Welcome to EduTECH
            </h1>
            <p className="text-gray-600 mb-8">
              Empowering Education Through Technology
            </p>
            <Link
              href="/register"
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-5 py-2 rounded-full font-medium hover:shadow-lg hover:shadow-blue-100 transition-all"
            >
              Get Started
            </Link>
          </div>
          <div className="lg:w-1/2 xl:w-1/3 p-8 bg-white/90 rounded-lg shadow-lg">
            <img
              src="/logo.png"
              alt="Hero Image"
              className="w-full mx-auto max-w-sm h-full object-cover rounded-lg"
            />
          </div>
        </div>
      </div>
    </section>
  );
};

const AboutSection = () => {
  return (
    <section id="about" className="py-20 bg-white">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            About EduTECH
          </h2>
          <div className="w-24 h-1 bg-gradient-to-r from-blue-500 to-indigo-600 mx-auto rounded-full"></div>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-100">
            <img
              src="https://images.unsplash.com/photo-1587560699334-f186d9d717c2?ixlib=rb-1.2.1&auto=format&fit=crop&w=1650&q=80"
              alt="About Image"
              className="w-full h-full object-cover rounded-lg"
            />
          </div>
          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-100">
            <p className="text-gray-600 mb-8">
              EduTECH is a comprehensive platform designed to simplify the
              management of educational institutions.
            </p>
            <p className="text-gray-600">
              Whether you are an administrator, staff, or student, EduTECH
              provides the tools you need to succeed in the digital age of
              education.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

const CallToAction = () => {
  return (
    <section className="py-20 bg-gray-800 text-white text-center">
      <h2 className="text-4xl font-bold mb-4">
        Ready to Transform Your School?
      </h2>
      <Link
        href="/register"
        className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-5 py-2 rounded-full font-medium hover:shadow-lg hover:shadow-blue-100 transition-all"
      >
        Get Started
      </Link>
    </section>
  );
};

const ContactSection = () => {
  return (
    <section id="contact" className="py-20 bg-white">
      <div className="container mx-auto px-6">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">Contact Us</h2>
          <div className="w-24 h-1 bg-gradient-to-r from-blue-500 to-indigo-600 mx-auto rounded-full"></div>
        </div>

        <div className="grid md:grid-cols-2 gap-8">
          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-100">
            <form
              action="/submit_form/"
              method="post"
              className="max-w-md mx-auto"
            >
              <div className="mb-4">
                <label
                  htmlFor="name"
                  className="block text-left font-semibold mb-2"
                >
                  Name:
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  required
                  className="w-full border border-gray-300 p-2 rounded-lg"
                />
              </div>
              <div className="mb-4">
                <label
                  htmlFor="email"
                  className="block text-left font-semibold mb-2"
                >
                  Email:
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  required
                  className="w-full border border-gray-300 p-2 rounded-lg"
                />
              </div>
              <div className="mb-4">
                <label
                  htmlFor="message"
                  className="block text-left font-semibold mb-2"
                >
                  Message:
                </label>
                <textarea
                  id="message"
                  name="message"
                  rows={4}
                  required
                  className="w-full border border-gray-300 p-2 rounded-lg"
                ></textarea>
              </div>
              <button
                type="submit"
                className="bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded-lg"
              >
                Send Message
              </button>
            </form>
          </div>
          <div className="bg-white p-8 rounded-xl shadow-lg hover:shadow-xl transition-shadow duration-300 border border-gray-100">
            <p className="text-gray-600 mb-8">
              Get in touch with us to learn more about how EduTECH can help your
              school succeed.
            </p>
            <p className="text-gray-600">
              Email:{" "}
              <a
                href="mailto:info@edutech.com"
                className="text-blue-600 hover:text-blue-800 transition-colors"
              >
                info@edutech.com
              </a>
            </p>
            <p className="text-gray-600">
              Phone:{" "}
              <a
                href="tel:+1234567890"
                className="text-blue-600 hover:text-blue-800 transition-colors"
              >
                +1234567890
              </a>
            </p>
          </div>
        </div>
      </div>
    </section>
  );
};

const Footer = () => {
  return (
    <footer className="bg-gray-700 text-gray-300 text-center py-4">
      <p>&copy; 2024 EduTECH. All rights reserved.</p>
    </footer>
  );
};

export {
  Header,
  HeroSection,
  AboutSection,
  CallToAction,
  ContactSection,
  Footer,
};
