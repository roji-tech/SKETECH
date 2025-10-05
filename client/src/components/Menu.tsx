"use client";

import { role } from "@/lib/data";
import { getActualPath } from "@/lib/utils";
import Image from "next/image";
import Link from "next/link";
import { signOut } from "next-auth/react";
import { useRouter } from "next/navigation";
import { customSignOut } from "@/actions/auth";

export const menuItems = [
  {
    title: "MENU",
    items: [
      {
        icon: "/home.png",
        label: "Home",
        href: `${getActualPath("/dashboard")}`,
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
      {
        icon: "/teacher.png",
        label: "Staff",
        href: `${getActualPath("/list/staff")}`,
        visible: ["owner", "admin", "staff"],
      },
      {
        icon: "/student.png",
        label: "Students",
        href: `${getActualPath("/list/students")}`,
        visible: ["owner", "admin", "staff"],
      },
      {
        icon: "/parent.png",
        label: "Parents",
        href: `${getActualPath("/list/parents")}`,
        visible: [ "owner", "admin", "staff"],
      },
      {
        icon: "/subject.png",
        label: "Subjects",
        href: `${getActualPath("/list/subjects")}`,
        visible: ["owner","admin"],
      },
      {
        icon: "/class.png",
        label: "Classes",
        href: `${getActualPath("/list/classes")}`,
        visible: ["owner", "admin", "staff"],
      },
      {
        icon: "/lesson.png",
        label: "Lessons",
        href: `${getActualPath("/list/lessons")}`,
        visible: ["owner", "admin", "staff"],
      },
      {
        icon: "/exam.png",
        label: "Exams",
        href: `${getActualPath("/list/exams")}`,
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
      {
        icon: "/assignment.png",
        label: "Assignments",
        href: `${getActualPath("/list/assignments")}`,
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
      {
        icon: "/result.png",
        label: "Results",
        href: `${getActualPath("/list/results")}`,
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
      {
        icon: "/attendance.png",
        label: "Attendance",
        href: `${getActualPath("/list/attendance")}`,
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
      {
        icon: "/calendar.png",
        label: "Events",
        href: `${getActualPath("/list/events")}`,
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
      {
        icon: "/message.png",
        label: "Messages",
        href: `${getActualPath("/list/messages")}`,
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
      {
        icon: "/announcement.png",
        label: "Announcements",
        href: `${getActualPath("/list/announcements")}`,
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
    ],
  },
  {
    title: "OTHER",
    items: [
      {
        icon: "/profile.png",
        label: "Profile",
        href: "/profile",
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
      {
        icon: "/setting.png",
        label: "Settings",
        href: "/settings",
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
      {
        icon: "/logout.png",
        label: "Logout",
        href: "/login",
        visible: ["owner", "admin", "staff", "student", "parent"],
      },
    ],
  },
];

const Menu = () => {
  const router = useRouter();

  const handleLogout = async (e: React.MouseEvent, href: string) => {
    if (href === "/login") {
      e.preventDefault();
      await customSignOut();
      await signOut({ callbackUrl: "/login" });
    }

    router.push(href);
  };

  return (
    <div className="mt-1 text-sm flex flex-col gap-2">
      {menuItems.map((i: any) => (
        <div className="flex flex-col gap-2" key={i.title}>
          <span className="hidden lg:block text-gray-400 font-light my-1">
            {i.title}
          </span>
          {i.items.map((item: any) => {
            if (item.visible.includes(role)) {
              return (
                <div
                  key={item.label}
                  title={item.label}
                  onClick={(e) => handleLogout(e, item.href)}
                  className="cursor-pointer flex items-center justify-center lg:justify-start gap-3 text-gray-500 py-2 md:px-1 rounded-md hover:bg-schSkyLight"
                >
                  <Image src={item.icon} alt="" width={20} height={20} />
                  <span className="hidden lg:block"> {item.label} </span>
                </div>
              );
            }
          })}
        </div>
      ))}
    </div>
  );
};

export default Menu;
