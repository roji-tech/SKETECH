"use client";

import React, { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";
import { apiGet } from "@/actions/fetchApi";

// Types for our dashboard data
type DashboardData = {
  upcoming_events: Array<{
    id: number;
    title: string;
    start_date: string;
    end_date: string;
    description: string;
  }>;
  announcements: Array<{
    id: number;
    title: string;
    content: string;
    created_at: string;
    created_by: string | null;
  }>;
  total_students?: number;
  total_staff?: number;
  total_classes?: number;
  attendance_rate?: number;
  total_fees_collected?: number;
  total_fees_pending?: number;
  recent_activities?: Array<{
    id: number;
    action: string;
    timestamp: string;
    user: string;
    details: string;
  }>;
  my_classes?: Array<{
    id: number;
    name: string;
    section: string;
    subject: string | null;
  }>;
  todays_schedule?: Array<{
    id: number;
    subject: string;
    class_group: string;
    start_time: string;
    end_time: string;
    teacher?: string;
  }>;
  assignments_to_grade?: number;
  upcoming_assignments?: Array<{
    id: number;
    title: string;
    subject: string;
    due_date: string;
    status: string;
  }>;
  recent_grades?: Array<{
    subject: string;
    grade: string;
    comments: string;
    date: string;
  }>;
  attendance_summary?: {
    present: number;
    absent: number;
    late: number;
  };
  children?: Array<{
    id: number;
    name: string;
    class: string;
    fees_paid: number;
    fees_due: number;
    attendance: {
      present: number;
      absent: number;
      late: number;
    };
  }>;
};

const DashboardPage = () => {
  const { data: session, status } = useSession();
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(
    null
  );
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setIsLoading(true);
        const response = await apiGet("/dashboard/");
        console.log("Dashboard Data:", response);
        setDashboardData(response.data);
        setError(null);
      } catch (err) {
        console.error("Failed to fetch dashboard data:", err);
        setError("Failed to load dashboard data. Please try again later.");
      } finally {
        setIsLoading(false);
      }
    };

    if (status === "authenticated") {
      fetchDashboardData();
    }
  }, [status]);

  // Loading state
  if (status === "loading" || isLoading) {
    return (
      <div className="p-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          {[...Array(4)].map((_, i) => (
            <Skeleton key={i} className="h-32 rounded-lg" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-96 rounded-lg" />
          <Skeleton className="h-96 rounded-lg" />
          <Skeleton className="h-96 rounded-lg" />
        </div>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="p-4">
        <div
          className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative"
          role="alert"
        >
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      </div>
    );
  }

  // Not authenticated
  if (!session) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold mb-2">Access Denied</h2>
          <p>Please log in to view the dashboard</p>
        </div>
      </div>
    );
  }

  const userRole = session.user.role;
  const data = dashboardData as DashboardData;

  // Render role-specific dashboard
  const renderAdminDashboard = () => (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="Total Students"
          value={data?.total_students?.toLocaleString() || "0"}
          icon="👥"
        />
        <StatCard
          title="Total Staff"
          value={data?.total_staff?.toLocaleString() || "0"}
          icon="👨‍🏫"
        />
        <StatCard
          title="Total Classes"
          value={data?.total_classes?.toLocaleString() || "0"}
          icon="🏫"
        />
        <StatCard
          title="Fees Collected"
          value={`$${data?.total_fees_collected?.toLocaleString() || "0"}`}
          icon="💰"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Recent Activities</CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-80">
              <div className="space-y-4">
                {data?.recent_activities?.map((activity) => (
                  <div key={activity.id} className="border-b pb-2">
                    <div className="flex justify-between">
                      <span className="font-medium">{activity.user}</span>
                      <span className="text-sm text-gray-500">
                        {new Date(activity.timestamp).toLocaleString()}
                      </span>
                    </div>
                    <p className="text-sm">{activity.action}</p>
                    {activity.details && (
                      <p className="text-xs text-gray-500">
                        {activity.details}
                      </p>
                    )}
                  </div>
                ))}
                {!data?.recent_activities?.length && (
                  <p className="text-gray-500 text-center py-4">
                    No recent activities
                  </p>
                )}
              </div>
            </ScrollArea>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <UpcomingEvents events={data?.upcoming_events} />
          <Announcements announcements={data?.announcements} />
        </div>
      </div>
    </>
  );

  const renderStaffDashboard = () => (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard
          title="My Classes"
          value={data?.my_classes?.length.toString() || "0"}
          icon="📚"
        />
        <StatCard
          title="Total Students"
          value={data?.total_students?.toLocaleString() || "0"}
          icon="👥"
        />
        <StatCard
          title="Today's Classes"
          value={data?.todays_schedule?.length.toString() || "0"}
          icon="📅"
        />
        <StatCard
          title="Assignments to Grade"
          value={data?.assignments_to_grade?.toString() || "0"}
          icon="📝"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="col-span-2">
          <CardHeader>
            <CardTitle>Today's Schedule</CardTitle>
          </CardHeader>
          <CardContent>
            {data?.todays_schedule?.length ? (
              <div className="space-y-4">
                {data?.todays_schedule.map((cls) => (
                  <div key={cls.id} className="border-b pb-2">
                    <div className="flex justify-between">
                      <span className="font-medium">{cls.subject}</span>
                      <span className="text-sm text-gray-500">
                        {cls.start_time} - {cls.end_time}
                      </span>
                    </div>
                    <p className="text-sm">{cls.class_group}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-4">
                No classes scheduled for today
              </p>
            )}
          </CardContent>
        </Card>

        <div className="space-y-6">
          <UpcomingEvents events={data?.upcoming_events} />
          <Announcements announcements={data?.announcements} />
        </div>
      </div>
    </>
  );

  const renderStudentDashboard = () => (
    <>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {data?.attendance_summary && (
          <>
            <StatCard
              title="Present"
              value={data?.attendance_summary.present.toString()}
              icon="✅"
            />
            <StatCard
              title="Absent"
              value={data?.attendance_summary.absent.toString()}
              icon="❌"
            />
            <StatCard
              title="Late"
              value={data?.attendance_summary.late.toString()}
              icon="⏰"
            />
          </>
        )}
        <StatCard
          title="Upcoming Assignments"
          value={data?.upcoming_assignments?.length.toString() || "0"}
          icon="📚"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {data?.todays_schedule && data?.todays_schedule.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Today's Schedule</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {data.todays_schedule.map((cls) => (
                    <div key={cls.id} className="border-b pb-2">
                      <div className="flex justify-between">
                        <span className="font-medium">{cls.subject}</span>
                        <span className="text-sm text-gray-500">
                          {cls.start_time} - {cls.end_time}
                        </span>
                      </div>
                      <p className="text-sm">
                        Teacher: {cls?.teacher! || "Not Assigned"}
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {data?.upcoming_assignments &&
            data?.upcoming_assignments.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Upcoming Assignments</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {data.upcoming_assignments.map((assignment) => (
                      <div key={assignment.id} className="border-b pb-2">
                        <div className="flex justify-between">
                          <span className="font-medium">
                            {assignment.title}
                          </span>
                          <span className="text-sm text-gray-500">
                            Due:{" "}
                            {new Date(assignment.due_date).toLocaleDateString()}
                          </span>
                        </div>
                        <p className="text-sm">{assignment.subject}</p>
                        <p className="text-xs text-gray-500">
                          Status: {assignment.status}
                        </p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
        </div>

        <div className="space-y-6">
          <UpcomingEvents events={data.upcoming_events} />
          <Announcements announcements={data.announcements} />
        </div>
      </div>
    </>
  );

  const renderParentDashboard = () => (
    <>
      <h2 className="text-2xl font-bold mb-6">My Children</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        {data.children?.map((child) => (
          <Card key={child.id}>
            <CardHeader>
              <CardTitle className="text-lg">{child.name}</CardTitle>
              <p className="text-sm text-gray-500">{child.class}</p>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div>
                  <p className="text-sm font-medium">Fees</p>
                  <div className="flex justify-between text-sm">
                    <span>Paid:</span>
                    <span>${child.fees_paid.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Due:</span>
                    <span>${child.fees_due.toLocaleString()}</span>
                  </div>
                </div>
                <div className="pt-2 border-t">
                  <p className="text-sm font-medium">Attendance</p>
                  <div className="flex justify-between text-sm">
                    <span>Present:</span>
                    <span>{child.attendance.present}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Absent:</span>
                    <span>{child.attendance.absent}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Late:</span>
                    <span>{child.attendance.late}</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Children's Upcoming Assignments</CardTitle>
            </CardHeader>
            <CardContent>
              {data.upcoming_assignments?.length ? (
                <div className="space-y-4">
                  {data.upcoming_assignments.map((assignment) => (
                    <div key={assignment.id} className="border-b pb-2">
                      <div className="flex justify-between">
                        <span className="font-medium">{assignment.title}</span>
                        <span className="text-sm text-gray-500">
                          Due:{" "}
                          {new Date(assignment.due_date).toLocaleDateString()}
                        </span>
                      </div>
                      <p className="text-sm">{assignment.subject}</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">
                  No upcoming assignments
                </p>
              )}
            </CardContent>
          </Card>
        </div>

        <div className="space-y-6">
          <UpcomingEvents events={data.upcoming_events} />
          <Announcements announcements={data?.announcements} />
        </div>
      </div>
    </>
  );

  // Render the appropriate dashboard based on user role
  const renderDashboard = () => {
    if (
      userRole === "admin" ||
      userRole === "owner" ||
      userRole === "superadmin"
    ) {
      return renderAdminDashboard();
    } else if (userRole === "staff") {
      return renderStaffDashboard();
    } else if (userRole === "student") {
      return renderStudentDashboard();
    } else if (userRole === "parent") {
      return renderParentDashboard();
    }
    return null;
  };

  return (
    <div className="p-4">
      <h1 className="text-3xl font-bold mb-6">
        Welcome back, {session.user?.firstName || "User"}!
      </h1>
      {renderDashboard()}
    </div>
  );
};

// Reusable Components
const StatCard = ({
  title,
  value,
  icon,
}: {
  title: string;
  value: string;
  icon: string;
}) => (
  <Card>
    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
      <CardTitle className="text-sm font-medium">{title}</CardTitle>
      <span className="text-2xl">{icon}</span>
    </CardHeader>
    <CardContent>
      <div className="text-2xl font-bold">{value}</div>
    </CardContent>
  </Card>
);

const UpcomingEvents = ({
  events,
}: {
  events?: Array<{
    id: number;
    title: string;
    start_date: string;
    end_date: string;
    description: string;
  }>;
}) => (
  <Card>
    <CardHeader>
      <CardTitle>Upcoming Events</CardTitle>
    </CardHeader>
    <CardContent>
      {events?.length ? (
        <div className="space-y-4">
          {events.map((event) => (
            <div
              key={event.id}
              className="border-b pb-2 last:border-0 last:pb-0"
            >
              <div className="flex justify-between">
                <h4 className="font-medium">{event.title}</h4>
                <span className="text-sm text-gray-500">
                  {new Date(event.start_date).toLocaleDateString()}
                  {event.end_date !== event.start_date &&
                    ` - ${new Date(event.end_date).toLocaleDateString()}`}
                </span>
              </div>
              <p className="text-sm text-gray-600 line-clamp-2">
                {event.description}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500 text-center py-4">No upcoming events</p>
      )}
    </CardContent>
  </Card>
);

const Announcements = ({
  announcements,
}: {
  announcements?: Array<{
    id: number;
    title: string;
    content: string;
    created_at: string;
    created_by: string | null;
  }>;
}) => (
  <Card>
    <CardHeader>
      <CardTitle>Announcements</CardTitle>
    </CardHeader>
    <CardContent>
      {announcements?.length ? (
        <ScrollArea className="h-64">
          <div className="space-y-4 pr-4">
            {announcements.map((announcement) => (
              <div
                key={announcement.id}
                className="border-b pb-2 last:border-0 last:pb-0"
              >
                <h4 className="font-medium">{announcement.title}</h4>
                <p className="text-sm text-gray-600 line-clamp-2">
                  {announcement.content}
                </p>
                <div className="flex justify-between mt-1">
                  <span className="text-xs text-gray-500">
                    {announcement.created_by || "System"}
                  </span>
                  <span className="text-xs text-gray-500">
                    {new Date(announcement.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </ScrollArea>
      ) : (
        <p className="text-gray-500 text-center py-4">No announcements</p>
      )}
    </CardContent>
  </Card>
);

export default DashboardPage;
