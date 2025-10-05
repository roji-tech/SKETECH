"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import Image from "next/image";

type Message = {
  id: string;
  sender: {
    id: string;
    name: string;
    image?: string;
    role: string;
  };
  content: string;
  timestamp: string;
  read: boolean;
};

type Participant = {
  id: string;
  name: string;
  image?: string;
  role: string;
};

type Conversation = {
  id: string;
  participants: Participant[];
  lastMessage: {
    content: string;
    timestamp: string;
    read: boolean;
  };
  unreadCount: number;
};

export default function MessagesPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [activeConversation, setActiveConversation] = useState<string | null>(
    null
  );
  const [message, setMessage] = useState("");
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (status === "authenticated") {
      const mockConversations: Conversation[] = [
        {
          id: "1",
          participants: [
            {
              id: "2",
              name: "John Doe",
              role: "teacher",
              image: "/avatar.png",
            },
          ],
          lastMessage: {
            content: "Hey, how are you doing?",
            timestamp: "10:30 AM",
            read: false,
          },
          unreadCount: 2,
        },
        {
          id: "2",
          participants: [
            {
              id: "3",
              name: "School Admin",
              role: "admin",
              image: "/avatar.png",
            },
          ],
          lastMessage: {
            content: "Meeting at 3 PM",
            timestamp: "Yesterday",
            read: true,
          },
          unreadCount: 0,
        },
      ];

      setConversations(mockConversations);
      setIsLoading(false);
    }
  }, [status]);

  useEffect(() => {
    if (activeConversation) {
      const mockMessages: Message[] = [
        {
          id: "1",
          sender: {
            id: "2",
            name: "John Doe",
            role: "teacher",
            image: "/avatar.png",
          },
          content: "Hey, how are you doing?",
          timestamp: "10:30 AM",
          read: true,
        },
        {
          id: "2",
          sender: {
            id: session?.user?.id || "current",
            name: "You",
            role: session?.user?.role || "student",
            ...(session?.user?.image && { image: session.user.image }),
          },
          content: "I'm doing great, thanks for asking! How about you?",
          timestamp: "10:32 AM",
          read: true,
        },
        {
          id: "3",
          sender: {
            id: "2",
            name: "John Doe",
            role: "teacher",
            image: "/avatar.png",
          },
          content: "All good here! Just checking in about the assignment.",
          timestamp: "10:33 AM",
          read: false,
        },
      ];

      setMessages(mockMessages);
    }
  }, [activeConversation, session]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      sender: {
        id: session?.user?.id || "current",
        name: "You",
        role: session?.user?.role || "student",
        ...(session?.user?.image && { image: session.user.image }),
      },
      content: message,
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      read: false,
    };

    setMessages([...messages, newMessage]);
    setMessage("");
  };

  if (status === "loading" || isLoading) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-200px)]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (status === "unauthenticated") {
    router.push("/login");
    return null;
  }

  return (
    <div className="flex h-[calc(100vh-80px)] bg-white rounded-lg shadow-sm overflow-hidden">
      {/* Conversations List */}
      <div className="w-full md:w-1/3 border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <h1 className="text-xl font-semibold text-gray-800">Messages</h1>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversations.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-gray-500">
              <Image
                src="/message-square.svg"
                alt="No messages"
                width={48}
                height={48}
                className="opacity-40 mb-2"
              />
              <p>No conversations yet</p>
            </div>
          ) : (
            conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={`p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50 ${
                  activeConversation === conversation.id ? "bg-blue-50" : ""
                }`}
                onClick={() => setActiveConversation(conversation.id)}
              >
                <div className="flex items-center">
                  <div className="relative">
                    <Image
                      src={conversation.participants[0]?.image || "/avatar.png"}
                      alt={conversation.participants[0]?.name || "User"}
                      width={40}
                      height={40}
                      className="rounded-full"
                      onError={(e) => {
                        const target = e.target as HTMLImageElement;
                        target.onerror = null;
                        target.src = "/avatar.png";
                      }}
                    />
                    {conversation.unreadCount > 0 && (
                      <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                        {conversation.unreadCount}
                      </span>
                    )}
                  </div>
                  <div className="ml-3 flex-1">
                    <div className="flex justify-between items-center">
                      <h3 className="text-sm font-medium text-gray-900">
                        {conversation.participants[0]?.name}
                      </h3>
                      <span className="text-xs text-gray-500">
                        {conversation.lastMessage.timestamp}
                      </span>
                    </div>
                    <p
                      className={`text-sm ${
                        conversation.lastMessage.read
                          ? "text-gray-500"
                          : "font-semibold text-gray-900"
                      }`}
                    >
                      {conversation.lastMessage.content.length > 30
                        ? `${conversation.lastMessage.content.substring(
                            0,
                            30
                          )}...`
                        : conversation.lastMessage.content}
                    </p>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat Area */}
      {activeConversation ? (
        <div className="hidden md:flex flex-col flex-1">
          {/* Chat Header */}
          <div className="p-4 border-b border-gray-200 flex items-center">
            <Image
              src={
                conversations.find((c) => c.id === activeConversation)
                  ?.participants[0]?.image || "/avatar.png"
              }
              alt={
                conversations.find((c) => c.id === activeConversation)
                  ?.participants[0]?.name || "User"
              }
              width={40}
              height={40}
              className="rounded-full"
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.onerror = null;
                target.src = "/avatar.png";
              }}
            />
            <div className="ml-3">
              <h2 className="text-lg font-medium text-gray-900">
                {
                  conversations.find((c) => c.id === activeConversation)
                    ?.participants[0]?.name
                }
              </h2>
              <p className="text-sm text-gray-500">
                {
                  conversations.find((c) => c.id === activeConversation)
                    ?.participants[0]?.role
                }
              </p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
            <div className="space-y-4">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex ${
                    msg.sender.id === session?.user?.id
                      ? "justify-end"
                      : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-xs md:max-w-md lg:max-w-lg px-4 py-2 rounded-lg ${
                      msg.sender.id === session?.user?.id
                        ? "bg-blue-600 text-white rounded-br-none"
                        : "bg-white border border-gray-200 rounded-bl-none"
                    }`}
                  >
                    {msg.sender.id !== session?.user?.id && (
                      <div className="text-xs font-medium text-gray-700 mb-1">
                        {msg.sender.name}
                      </div>
                    )}
                    <p className="text-sm">{msg.content}</p>
                    <div className="text-right mt-1">
                      <span className="text-xs opacity-70">
                        {msg.timestamp}
                        {msg.sender.id === session?.user?.id && (
                          <span className="ml-1">{msg.read ? "✓✓" : "✓"}</span>
                        )}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Message Input */}
          <div className="p-4 border-t border-gray-200">
            <form onSubmit={handleSendMessage} className="flex gap-2">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type a message..."
                className="flex-1 border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />
              <button
                type="submit"
                className="bg-blue-600 text-white rounded-full p-2 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                disabled={!message.trim()}
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </form>
          </div>
        </div>
      ) : (
        <div className="hidden md:flex flex-col items-center justify-center flex-1 bg-gray-50 text-gray-500">
          <Image
            src="/message-square.svg"
            alt="Select a conversation"
            width={64}
            height={64}
            className="opacity-30 mb-4"
          />
          <p className="text-lg font-medium">Select a conversation</p>
          <p className="text-sm mt-1">or start a new one</p>
        </div>
      )}

      {/* Mobile view - Show conversation or messages */}
      <div className="md:hidden w-full">
        {activeConversation ? (
          <div className="h-full flex flex-col">
            {/* Back button */}
            <div className="p-2 border-b border-gray-200 flex items-center">
              <button
                onClick={() => setActiveConversation(null)}
                className="p-2 rounded-full hover:bg-gray-100"
              >
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  className="h-5 w-5 text-gray-600"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                >
                  <path
                    fillRule="evenodd"
                    d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
              <h2 className="ml-2 font-medium">
                {
                  conversations.find((c) => c.id === activeConversation)
                    ?.participants[0]?.name
                }
              </h2>
            </div>

            {/* Messages */}
            <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
              <div className="space-y-4">
                {messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={`flex ${
                      msg.sender.id === session?.user?.id
                        ? "justify-end"
                        : "justify-start"
                    }`}
                  >
                    <div
                      className={`max-w-xs px-4 py-2 rounded-lg ${
                        msg.sender.id === session?.user?.id
                          ? "bg-blue-600 text-white rounded-br-none"
                          : "bg-white border border-gray-200 rounded-bl-none"
                      }`}
                    >
                      {msg.sender.id !== session?.user?.id && (
                        <div className="text-xs font-medium text-gray-700 mb-1">
                          {msg.sender.name}
                        </div>
                      )}
                      <p className="text-sm">{msg.content}</p>
                      <div className="text-right mt-1">
                        <span className="text-xs opacity-70">
                          {msg.timestamp}
                          {msg.sender.id === session?.user?.id && (
                            <span className="ml-1">
                              {msg.read ? "✓✓" : "✓"}
                            </span>
                          )}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Message Input */}
            <div className="p-4 border-t border-gray-200 bg-white">
              <form onSubmit={handleSendMessage} className="flex gap-2">
                <input
                  type="text"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Type a message..."
                  className="flex-1 border border-gray-300 rounded-full px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
                />
                <button
                  type="submit"
                  className="bg-blue-600 text-white rounded-full p-2 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                  disabled={!message.trim()}
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    className="h-5 w-5"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.707l-3-3a1 1 0 00-1.414 1.414L10.586 9H7a1 1 0 100 2h3.586l-1.293 1.293a1 1 0 101.414 1.414l3-3a1 1 0 000-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>
              </form>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col">
            <div className="p-4 border-b border-gray-200">
              <h1 className="text-xl font-semibold text-gray-800">Messages</h1>
            </div>

            <div className="flex-1 overflow-y-auto">
              {conversations.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-500 p-4 text-center">
                  <Image
                    src="/message-square.svg"
                    alt="No messages"
                    width={48}
                    height={48}
                    className="opacity-40 mb-2"
                  />
                  <p className="font-medium">No conversations yet</p>
                  <p className="text-sm mt-1">
                    Start a new conversation with your contacts
                  </p>
                </div>
              ) : (
                conversations.map((conversation) => (
                  <div
                    key={conversation.id}
                    className="p-4 border-b border-gray-100 cursor-pointer hover:bg-gray-50"
                    onClick={() => setActiveConversation(conversation.id)}
                  >
                    <div className="flex items-center">
                      <div className="relative">
                        <Image
                          src={
                            conversation.participants[0]?.image || "/avatar.png"
                          }
                          alt={conversation.participants[0]?.name || "User"}
                          width={48}
                          height={48}
                          className="rounded-full"
                          onError={(e) => {
                            const target = e.target as HTMLImageElement;
                            target.onerror = null;
                            target.src = "/avatar.png";
                          }}
                        />
                        {conversation.unreadCount > 0 && (
                          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                            {conversation.unreadCount}
                          </span>
                        )}
                      </div>
                      <div className="ml-3 flex-1">
                        <div className="flex justify-between items-center">
                          <h3 className="text-sm font-medium text-gray-900">
                            {conversation.participants[0]?.name}
                          </h3>
                          <span className="text-xs text-gray-500">
                            {conversation.lastMessage.timestamp}
                          </span>
                        </div>
                        <p
                          className={`text-sm ${
                            conversation.lastMessage.read
                              ? "text-gray-500"
                              : "font-semibold text-gray-900"
                          }`}
                        >
                          {conversation.lastMessage.content.length > 30
                            ? `${conversation.lastMessage.content.substring(
                                0,
                                30
                              )}...`
                            : conversation.lastMessage.content}
                        </p>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
