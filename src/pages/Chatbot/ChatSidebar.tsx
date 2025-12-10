import { Button } from "../../components/ui/button";
import { ScrollArea } from "../../components/ui/scroll-area";
import { PlusCircle, MessageSquare, Trash2, Menu, X, Sparkles } from "lucide-react";
import { useSidebar } from "../../context/SidebarContext";

interface Chat {
  id: string;
  title: string;
  timestamp: Date;
}

interface ChatSidebarProps {
  chats: Chat[];
  currentChatId: string | null;
  onSelectChat: (id: string) => void;
  onNewChat: () => void;
  onDeleteChat: (id: string) => void;
}

export function ChatSidebar({
  chats,
  currentChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
}: ChatSidebarProps) {
  const { isCollapsed } = useSidebar();

  return (
    <div
      className={`hidden lg:flex h-full flex-col bg-gradient-to-b from-pink-50 via-rose-50 to-pink-100 border-r-2 border-pink-200 transition-all duration-300 ${
        isCollapsed ? "w-16" : "w-64"
      }`}
    >
      {/* Header */}
      <div className={`border-b border-pink-200 bg-gradient-to-r from-pink-100 to-rose-100 ${isCollapsed ? "p-2" : "p-3"}`}>
        <Button
          onClick={onNewChat}
          className={`bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white shadow-lg rounded-xl ${
            isCollapsed ? "w-full p-2" : "w-full"
          }`}
          size={isCollapsed ? "icon" : "default"}
        >
          <Sparkles className={`h-4 w-4 ${isCollapsed ? "" : "mr-2"}`} />
          {!isCollapsed && "New Chat"}
        </Button>
      </div>

      {/* Chat List */}
      <ScrollArea className="flex-1">
        <div className={`space-y-1 ${isCollapsed ? "p-1" : "p-2"}`}>
          {chats.length === 0 ? (
            !isCollapsed && (
              <div className="text-center py-8 text-pink-400 text-sm">
                Chưa có cuộc trò chuyện nào
              </div>
            )
          ) : (
            chats.map((chat) => (
              <div
                key={chat.id}
                className={`group relative flex items-center rounded-xl cursor-pointer transition-all ${
                  isCollapsed ? "p-2 justify-center" : "gap-3 p-3"
                } ${
                  currentChatId === chat.id
                    ? "bg-gradient-to-r from-pink-200 to-rose-200 border border-pink-300 shadow-md"
                    : "hover:bg-pink-100 border border-transparent"
                }`}
                onClick={() => onSelectChat(chat.id)}
                title={isCollapsed ? chat.title : undefined}
              >
                <MessageSquare className={`h-4 w-4 flex-shrink-0 ${
                  currentChatId === chat.id ? "text-pink-600" : "text-pink-400"
                }`} />
                {!isCollapsed && (
                  <>
                    <div className="flex-1 min-w-0">
                      <span className={`text-sm truncate block ${
                        currentChatId === chat.id ? "text-pink-800 font-medium" : "text-pink-700"
                      }`}>
                        {chat.title}
                      </span>
                      <span className="text-xs text-pink-400">
                        {chat.timestamp.toLocaleDateString('vi-VN')}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-100"
                      onClick={(e: React.MouseEvent) => {
                        e.stopPropagation();
                        onDeleteChat(chat.id);
                      }}
                    >
                      <Trash2 className="h-3.5 w-3.5 text-pink-400 hover:text-red-500" />
                    </Button>
                  </>
                )}
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Footer */}
      {!isCollapsed && (
        <div className="p-3 border-t border-pink-200 bg-gradient-to-r from-pink-50 to-rose-50">
          <div className="text-center text-xs text-pink-500">
            🍜 Smart Travel AI Assistant
          </div>
        </div>
      )}
    </div>
  );
}
