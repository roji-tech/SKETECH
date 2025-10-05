import Announcements from "@/components/Announcements";
import BigCalendar from "@/components/BigCalender";

const ParentPage = () => {
  return (
    <div className="flex-1 p-4 flex gap-4 flex-col xl:flex-row">
      {/* LEFT */}
      <div className="w-full xl:w-2/3">
        <div className="h-full bg-white p-4 rounded-md">
          <h1 className="text-xl font-semibold">Schedule (John Doe)</h1>
          <BigCalendar />
        </div>
      </div>
      {/* RIGHT */}
      <div className="w-full xl:w-1/3 flex flex-col gap-8">
        <Announcements />
      </div>
    </div>
  );
};

export default ParentPage;

// "use client";

// import React, { useState } from "react";

// const SettingsPage = () => {
//   const [settings, setSettings] = useState({
//     notifications: true,
//     darkMode: false,
//     language: "English",
//   });

//   const handleToggle = (key: string) => {
//     setSettings((prev) => ({ ...prev, [key]: !prev[key] }));
//   };

//   return (
//     <div className="p-4">
//       <h2 className="text-lg font-semibold mb-4">Settings</h2>
//       <div className="space-y-6">
//         {/* Notifications */}
//         <div className="flex items-center justify-between bg-white p-4 rounded-lg shadow-md">
//           <div>
//             <h4 className="font-semibold">Notifications</h4>
//             <p className="text-sm text-gray-500">Enable or disable notifications</p>
//           </div>
//           <button
//             onClick={() => handleToggle("notifications")}
//             className={`w-10 h-6 flex items-center rounded-full ${
//               settings.notifications ? "bg-green-500" : "bg-gray-300"
//             }`}
//           >
//             <div
//               className={`w-4 h-4 bg-white rounded-full shadow-md transform transition-transform ${
//                 settings.notifications ? "translate-x-4" : ""
//               }`}
//             ></div>
//           </button>
//         </div>

//         {/* Dark Mode */}
//         <div className="flex items-center justify-between bg-white p-4 rounded-lg shadow-md">
//           <div>
//             <h4 className="font-semibold">Dark Mode</h4>
//             <p className="text-sm text-gray-500">Switch between light and dark mode</p>
//           </div>
//           <button
//             onClick={() => handleToggle("darkMode")}
//             className={`w-10 h-6 flex items-center rounded-full ${
//               settings.darkMode ? "bg-green-500" : "bg-gray-300"
//             }`}
//           >
//             <div
//               className={`w-4 h-4 bg-white rounded-full shadow-md transform transition-transform ${
//                 settings.darkMode ? "translate-x-4" : ""
//               }`}
//             ></div>
//           </button>
//         </div>

//         {/* Language */}
//         <div className="bg-white p-4 rounded-lg shadow-md">
//           <h4 className="font-semibold mb-2">Language</h4>
//           <select
//             value={settings.language}
//             onChange={(e) =>
//               setSettings((prev) => ({ ...prev, language: e.target.value }))
//             }
//             className="block w-full border-gray-300 rounded-md shadow-sm"
//           >
//             <option>English</option>
//             <option>Spanish</option>
//             <option>French</option>
//             <option>German</option>
//           </select>
//         </div>
//       </div>
//     </div>
//   );
// };

// export default SettingsPage;
