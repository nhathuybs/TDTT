import { useState, useEffect, useRef } from "react";
import { Routes, Route, useNavigate, useLocation, useParams } from "react-router-dom";

// Pages imports
import {
  HomePage,
  RestaurantList,
  RestaurantDetail,
  MenuPage,
  AboutPage,
  ContactPage,
  PolicyPage,
  ProfilePage,
  SettingsPage,
  PremiumPage,
  ChatSidebar,
  ChatMessage,
  ChatInput,
  PromptSuggestions,
  FloatingChatbot
} from "./pages";

// Common components
import { AuthDialog } from "./components/AuthDialog";
import { UserMenu } from "./components/UserMenu";
import { Navigation } from "./components/Navigation";

// UI components
import { ScrollArea } from "./components/ui/scroll-area";
import { Button } from "./components/ui/button";
import { Toaster } from "./components/ui/sonner";
import { UtensilsCrossed } from "lucide-react";

// Services & Context
import { fetchAllRestaurants, fetchRestaurantById, recommendRestaurantsForChat, Restaurant as ApiRestaurant } from "./services/api";
import type { LoginResponse } from "./services/auth";
import { SidebarProvider, useSidebar } from "./context/SidebarContext";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  recommendations?: ChatRecommendationRestaurant[];
}

interface Chat {
  id: string;
  title: string;
  timestamp: Date;
  messages: Message[];
}

interface ChatRecommendationRestaurant {
  id: string;
  name: string;
  cuisine?: string;
  address?: string;
  rating?: number;
  reviewCount?: number;
  priceLevel?: number;
  image?: string;
  googleMapsUrl?: string;
}

interface User {
  email: string;
  name: string;
  avatar?: string | null;
}

const AUTH_STORAGE_KEY = "auth";

// Use Restaurant type from API service
type Restaurant = ApiRestaurant;

// Mock travel food AI responses
const travelFoodResponses = [
  "Dựa trên vị trí của bạn, tôi gợi ý thử phở tại Phở Hà Nội - một trong những quán phở truyền thống tốt nhất với nước dùng nguyên bản!",
  "Bánh mì Sài Gòn gần đây là lựa chọn tuyệt vời cho bữa sáng! Họ mở cửa từ 6:00 sáng với bánh mì giòn tan và nhiều loại nhân đa dạng.",
  "Nếu bạn thích hải sản, Nhà Hàng Hải Sản Biển Xanh là nơi hoàn hảo với tôm hấp và cua rang me tuyệt ngon!",
  "Món bún chả tại Phở Hà Nội rất đáng thử! Thịt nướng thơm phức với nước chấm đặc biệt là điểm nhấn của món này.",
  "Cơm tấm Sài Gòn là lựa chọn tốt cho bữa trưa với giá phải chăng chỉ từ 50-55k. Sườn nướng và bì rất ngon!",
  "Nếu bạn ăn chay, Nhà Hàng Chay Sen Việt có nhiều món chay sáng tạo và ngon miệng. Phở chay của họ rất được yêu thích!",
];

function generateId() {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

// Restaurant Detail Page Wrapper
function RestaurantDetailPage() {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadRestaurant = async () => {
      if (id) {
        setLoading(true);
        const data = await fetchRestaurantById(id);
        setRestaurant(data);
        setLoading(false);
      }
    };
    loadRestaurant();
  }, [id]);
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-app">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-500"></div>
      </div>
    );
  }
  
  if (!restaurant) {
    return (
      <div className="flex flex-col items-center justify-center h-app">
        <p className="text-pink-600 mb-4">Không tìm thấy nhà hàng</p>
        <Button onClick={() => navigate('/restaurants')}>Quay lại danh sách</Button>
      </div>
    );
  }
  
  return <RestaurantDetail restaurant={restaurant} onBack={() => navigate('/restaurants')} />;
}

// Restaurant List Page Wrapper
function RestaurantListPage() {
  const navigate = useNavigate();
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  
  useEffect(() => {
    const loadRestaurants = async () => {
      setIsLoading(true);
      try {
        const data = await fetchAllRestaurants(100);
        setRestaurants(data);
      } catch (error) {
        console.error('Failed to fetch restaurants:', error);
      } finally {
        setIsLoading(false);
      }
    };
    loadRestaurants();
  }, []);
  
  const handleSelectRestaurant = (restaurant: Restaurant) => {
    navigate(`/restaurants/${restaurant.id}`);
  };
  
  return <RestaurantList restaurants={restaurants} onSelectRestaurant={handleSelectRestaurant} isLoading={isLoading} />;
}

// Home Page Wrapper
function HomePageWrapper() {
  const navigate = useNavigate();
  return (
    <HomePage
      onNavigateToRestaurants={() => navigate("/restaurants")}
      onNavigateToChatbot={() => navigate("/chatbot")}
    />
  );
}

// Chatbot Page Component
function ChatbotPage() {
  const [chats, setChats] = useState<Chat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  const currentChat = chats.find((chat) => chat.id === currentChatId);

  useEffect(() => {
    if (chats.length === 0) {
      handleNewChat();
    }
  }, []);

  useEffect(() => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector("[data-radix-scroll-area-viewport]");
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [currentChat?.messages]);

  const handleNewChat = () => {
    const newChat: Chat = {
      id: generateId(),
      title: "New Chat",
      timestamp: new Date(),
      messages: [],
    };
    setChats((prev) => [newChat, ...prev]);
    setCurrentChatId(newChat.id);
  };

  const handleSelectChat = (id: string) => {
    setCurrentChatId(id);
  };

  const handleDeleteChat = (id: string) => {
    setChats((prev) => prev.filter((chat) => chat.id !== id));
    if (currentChatId === id) {
      const remainingChats = chats.filter((chat) => chat.id !== id);
      setCurrentChatId(remainingChats[0]?.id || null);
      if (remainingChats.length === 0) {
        handleNewChat();
      }
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!currentChatId) return;

    const userMessage: Message = {
      id: generateId(),
      role: "user",
      content,
    };

    setChats((prev) =>
      prev.map((chat) => {
        if (chat.id === currentChatId) {
          const updatedMessages = [...chat.messages, userMessage];
          const title =
            chat.messages.length === 0
              ? content.slice(0, 30) + (content.length > 30 ? "..." : "")
              : chat.title;
          return { ...chat, messages: updatedMessages, title };
        }
        return chat;
      })
    );

    setIsGenerating(true);
    try {
      const data = await recommendRestaurantsForChat(content, 6);
      const recommendations: ChatRecommendationRestaurant[] = (data.restaurants || []).map((r) => ({
        id: r.id,
        name: r.name,
        cuisine: r.cuisine,
        address: r.address,
        rating: r.rating,
        reviewCount: r.review_count,
        priceLevel: r.price_level,
        image: r.image,
        googleMapsUrl: r.google_maps_url,
      }));

      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content: data.reply,
        recommendations,
      };

      setChats((prev) =>
        prev.map((chat) =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, assistantMessage] }
            : chat,
        ),
      );
    } catch (err: any) {
      const assistantMessage: Message = {
        id: generateId(),
        role: "assistant",
        content:
          err?.message ||
          "Xin lỗi, mình đang gặp lỗi khi gợi ý nhà hàng. Bạn thử lại giúp mình nhé.",
      };
      setChats((prev) =>
        prev.map((chat) =>
          chat.id === currentChatId
            ? { ...chat, messages: [...chat.messages, assistantMessage] }
            : chat,
        ),
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="flex h-screen w-full">
      {/* Chat History Sidebar - synced with Navigation */}
      <ChatSidebar
        chats={chats}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
      />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 relative h-screen">
        {currentChat ? (
          <>
            <ScrollArea className="flex-1" ref={scrollAreaRef}>
              <div className="max-w-3xl mx-auto pt-8 px-4">
                {currentChat.messages.length === 0 ? (
                  <div className="flex flex-col items-center justify-center min-h-[50vh] p-6">
                    <div className="flex items-center gap-3 mb-6">
                      <div
                        className="p-5 rounded-full bg-gradient-to-br from-pink-400 via-rose-400 to-fuchsia-400 shadow-2xl shadow-pink-400/60 animate-pulse border-4 border-pink-200"
                        style={{
                          animationDuration: "2s",
                          boxShadow: "0 0 40px rgba(255,182,193,0.6), inset 0 0 20px rgba(255,255,255,0.5)",
                        }}
                      >
                        <UtensilsCrossed className="h-12 w-12 text-white drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]" />
                      </div>
                    </div>
                    <div className="text-center space-y-3 mb-8">
                      <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
                        🍜 Trợ Lý Ẩm Thực AI 🥢
                      </h1>
                      <p className="text-pink-700 text-lg max-w-3xl mx-auto">
                        ✨ Hỏi tôi về món ăn Việt Nam và nhận gợi ý nhà hàng tuyệt vời! ✨
                      </p>
                    </div>
                    <PromptSuggestions onSelectPrompt={handleSendMessage} />
                  </div>
                ) : (
                  <div>
                    {currentChat.messages.map((message) => (
                      <ChatMessage
                        key={message.id}
                        role={message.role}
                        content={message.content}
                        recommendations={message.recommendations}
                      />
                    ))}
                    {isGenerating && (
                      <div
                        className="flex gap-4 p-6 bg-gradient-to-r from-pink-200/80 via-rose-200/80 to-fuchsia-200/80 backdrop-blur-md border-2 border-pink-300 rounded-3xl my-2 mx-4 shadow-lg"
                        style={{
                          boxShadow: "0 0 25px rgba(255,182,193,0.4), inset 0 0 20px rgba(255,255,255,0.3)",
                        }}
                      >
                        <div className="flex gap-2">
                          <div
                            className="w-4 h-4 bg-gradient-to-r from-pink-400 to-rose-400 rounded-full animate-bounce shadow-lg"
                            style={{ boxShadow: "0 0 12px rgba(255,182,193,0.6)" }}
                          />
                          <div
                            className="w-4 h-4 bg-gradient-to-r from-rose-400 to-fuchsia-400 rounded-full animate-bounce shadow-lg"
                            style={{ animationDelay: "0.2s", boxShadow: "0 0 12px rgba(255,182,193,0.6)" }}
                          />
                          <div
                            className="w-4 h-4 bg-gradient-to-r from-fuchsia-400 to-pink-400 rounded-full animate-bounce shadow-lg"
                            style={{ animationDelay: "0.4s", boxShadow: "0 0 12px rgba(255,182,193,0.6)" }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </ScrollArea>

            <ChatInput onSendMessage={handleSendMessage} disabled={isGenerating} />
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center">
            <p className="text-pink-600">Chọn chat hoặc tạo chat mới</p>
          </div>
        )}
      </div>
    </div>
  );
}

export default function App() {
  return (
    <SidebarProvider>
      <AppContent />
    </SidebarProvider>
  );
}

function AppContent() {
  const [user, setUser] = useState<User | null>(null);
  const [authDialogOpen, setAuthDialogOpen] = useState(false);
  const location = useLocation();
  const { isCollapsed } = useSidebar();

  useEffect(() => {
    const stored = localStorage.getItem(AUTH_STORAGE_KEY);
    if (!stored) return;
    try {
      const parsed = JSON.parse(stored) as { user?: { email?: string; name?: string; avatar?: string | null } } | null;
      const email = parsed?.user?.email;
      const name = parsed?.user?.name;
      if (email && name) {
        setUser({ email, name, avatar: parsed?.user?.avatar ?? null });
      }
    } catch {
      localStorage.removeItem(AUTH_STORAGE_KEY);
    }
  }, []);

  useEffect(() => {
    const handler = (event: Event) => {
      const detail = (event as CustomEvent).detail as { user?: { email?: string; name?: string; avatar?: string | null } } | undefined;
      const email = detail?.user?.email;
      const name = detail?.user?.name;
      if (email && name) {
        setUser({ email, name, avatar: detail?.user?.avatar ?? null });
      }
    };

    window.addEventListener("auth:updated", handler as EventListener);
    return () => window.removeEventListener("auth:updated", handler as EventListener);
  }, []);

  useEffect(() => {
    const handler = () => setAuthDialogOpen(true);
    window.addEventListener("auth:open", handler);
    return () => window.removeEventListener("auth:open", handler);
  }, []);

  const handleLogin = (payload: LoginResponse) => {
    setUser({ email: payload.user.email, name: payload.user.name, avatar: payload.user.avatar ?? null });
    localStorage.setItem(
      AUTH_STORAGE_KEY,
      JSON.stringify({
        user: payload.user,
        accessToken: payload.access_token,
        refreshToken: payload.refresh_token,
        expiresIn: payload.expires_in,
      }),
    );
  };

  const handleLogout = () => {
    setUser(null);
    localStorage.removeItem(AUTH_STORAGE_KEY);
  };

  // Check if current page is chatbot
  const isChatbotPage = location.pathname === '/chatbot';

  return (
    <div className="h-app flex bg-gradient-to-br from-pink-100 via-purple-100 to-fuchsia-100 text-gray-800 relative overflow-hidden">
      <Toaster position="top-center" />
      
      {/* Auth Dialog */}
      <AuthDialog open={authDialogOpen} onOpenChange={setAuthDialogOpen} onLogin={handleLogin} />

      {/* Navigation Sidebar */}
      <Navigation
        user={user}
        onLoginClick={() => setAuthDialogOpen(true)}
        onLogout={handleLogout}
      />

      {/* Pastel Pink Galaxy/Nebula Background */}
      <div className="fixed inset-0 bg-gradient-to-br from-pink-200/60 via-purple-200/50 to-fuchsia-200/60 pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-pink-300/40 via-transparent to-transparent pointer-events-none" />
      <div className="fixed inset-0 bg-[radial-gradient(ellipse_at_bottom_left,_var(--tw-gradient-stops))] from-fuchsia-300/40 via-transparent to-transparent pointer-events-none" />

      {/* Twinkling Pink Stars */}
      {[...Array(50)].map((_, i) => (
        <div
          key={`star-${i}`}
          className="star fixed pointer-events-none"
          style={{
            width: Math.random() * 4 + 2 + "px",
            height: Math.random() * 4 + 2 + "px",
            left: Math.random() * 100 + "%",
            top: Math.random() * 100 + "%",
            animationDelay: Math.random() * 3 + "s",
            animationDuration: Math.random() * 2 + 2 + "s",
            background:
              "radial-gradient(circle, rgba(255,182,193,1) 0%, rgba(255,105,180,0.9) 50%, transparent 100%)",
          }}
        />
      ))}

      {/* Floating Food Emojis */}
      <div className="food-emoji-float fixed top-10 left-20 text-6xl lg:left-72 pointer-events-none" style={{ animationDuration: "4s" }}>🍜</div>
      <div className="food-emoji-float fixed top-40 right-32 text-5xl pointer-events-none" style={{ animationDuration: "5s", animationDelay: "0.5s" }}>🥖</div>
      <div className="food-emoji-float fixed bottom-20 left-40 text-5xl lg:left-80 pointer-events-none" style={{ animationDuration: "4.5s", animationDelay: "1s" }}>🌶️</div>
      <div className="food-emoji-float fixed bottom-32 right-20 text-6xl pointer-events-none" style={{ animationDuration: "5.5s", animationDelay: "1.5s" }}>🥢</div>
      <div className="food-emoji-float fixed top-1/2 right-10 text-4xl pointer-events-none" style={{ animationDuration: "4s", animationDelay: "2s" }}>🍲</div>
      <div className="food-emoji-float fixed top-1/3 left-1/4 text-5xl pointer-events-none" style={{ animationDuration: "4.8s", animationDelay: "0.8s" }}>☕</div>
      <div className="food-emoji-float fixed bottom-1/4 right-1/3 text-4xl pointer-events-none" style={{ animationDuration: "5.2s", animationDelay: "1.2s" }}>🥘</div>

      {/* Main Content - with left margin for sidebar on desktop */}
      <div className={`flex-1 flex flex-col relative z-10 transition-all duration-300 ${isCollapsed ? "lg:ml-20" : "lg:ml-64"}`}>
        <Routes>
          <Route path="/" element={<HomePageWrapper />} />
          <Route path="/restaurants" element={<RestaurantListPage />} />
          <Route path="/restaurants/:id" element={<RestaurantDetailPage />} />
          <Route path="/menu" element={<MenuPage />} />
          <Route path="/chatbot" element={<ChatbotPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/contact" element={<ContactPage />} />
          <Route path="/policy" element={<PolicyPage />} />
          <Route path="/account/profile" element={<ProfilePage />} />
          <Route path="/account/settings" element={<SettingsPage />} />
          <Route path="/account/premium" element={<PremiumPage />} />
        </Routes>
      </div>

      {/* Floating Chatbot - only show on non-chatbot views */}
      {!isChatbotPage && <FloatingChatbot />}
    </div>
  );
}
