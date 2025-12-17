import { Button } from "../../components/ui/button";
import { Card } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { UtensilsCrossed, Search, Globe, MessageCircle, Star } from "lucide-react";
import { ImageWithFallback } from "../../components/figma/ImageWithFallback";

interface HomePageProps {
  onNavigateToRestaurants: () => void;
  onNavigateToChatbot: () => void;
}

const featuredDishes = [
  {
    name: "Phở Bò",
    image: "https://images.unsplash.com/photo-1701480253822-1842236c9a97?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwcGhvJTIwbm9vZGxlJTIwc291cHxlbnwxfHx8fDE3NjI0MDY1OTB8MA&ixlib=rb-4.1.0&q=80&w=1080",
    description: "Món phở truyền thống của Việt Nam với nước dùng thơm ngon",
  },
  {
    name: "Bánh Mì",
    image: "https://images.unsplash.com/photo-1599719455360-ff0be7c4dd06?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwYmFuaCUyMG1pJTIwc2FuZHdpY2h8ZW58MXx8fHwxNzYyNDA2NTkwfDA&ixlib=rb-4.1.0&q=80&w=1080",
    description: "Bánh mì Việt Nam với nhiều loại nhân thơm ngon",
  },
  {
    name: "Gỏi Cuốn",
    image: "https://images.unsplash.com/photo-1693494869603-09f1981f28e0?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHx2aWV0bmFtZXNlJTIwc3ByaW5nJTIwcm9sbHN8ZW58MXx8fHwxNzYyMzMyNjA2fDA&ixlib=rb-4.1.0&q=80&w=1080",
    description: "Gỏi cuốn tươi mát với tôm và rau sống",
  },
];

const features = [
  {
    icon: Search,
    title: "Tìm kiếm dễ dàng",
    description: "Tìm nhà hàng phù hợp với sở thích và ngân sách của bạn",
  },
  {
    icon: MessageCircle,
    title: "Chatbot AI hỗ trợ",
    description: "Mô hình hóa trợ lý cá nhân, người bạn đồng hành trong lĩnh vực ẩm thực",
  },
  {
    icon: Star,
    title: "Đánh giá chính xác",
    description: "Nói không với seeding, đảm bảo đánh giá khách quan và trung thực",
  },
  {
    icon: Globe, 
    title: "Thấu hiểu ngôn ngữ",
    description: "Xóa bỏ rào cản ngôn ngữ cho du khách với khả năng dịch thuật và giải thích văn hóa ẩm thực Việt tự động.",
  }
];

export function HomePage({ onNavigateToRestaurants, onNavigateToChatbot }: HomePageProps) {
  return (
    <div className="min-h-screen relative overflow-auto">
      <div className="max-w-7xl mx-auto p-4 md:p-6 space-y-12 pb-24">
        {/* Hero Section */}
        <div className="text-center space-y-6 pt-8">
          <div className="flex justify-center mb-6">
            <div
              className="p-8 rounded-full bg-gradient-to-br from-pink-400 via-rose-400 to-fuchsia-400 shadow-2xl animate-pulse border-4 border-pink-200"
              style={{
                animationDuration: "2s",
                boxShadow:
                  "0 0 60px rgba(255,182,193,0.8), inset 0 0 30px rgba(255,255,255,0.5)",
              }}
            >
              <UtensilsCrossed className="h-20 w-20 text-white drop-shadow-[0_0_15px_rgba(255,255,255,0.9)]" />
            </div>
          </div>

          <div className="space-y-4">
            <h1 className="bg-gradient-to-r from-pink-600 via-rose-600 to-fuchsia-600 bg-clip-text text-transparent drop-shadow-[0_2px_8px_rgba(255,182,193,0.4)]">
              🍜 Food Journey Assistant 🥢
            </h1>
            <p className="text-pink-700 text-lg max-w-3xl mx-auto">
              Hơn cả một bữa ăn, chúng tôi kể câu chuyện văn hóa qua lăng kính công nghệ
              <br />
              Để mỗi gợi ý đều là một "viên ngọc ẩn" dành riêng cho bạn 
            </p>
          </div>

          <div className="flex flex-wrap gap-4 justify-center">
            <Button
              onClick={onNavigateToRestaurants}
              className="bg-gradient-to-r from-pink-400 to-rose-400 hover:from-pink-500 hover:to-rose-500 text-white rounded-2xl px-8 py-6 shadow-xl font-bold"
              style={{ boxShadow: "0 0 30px rgba(255,182,193,0.6)" }}
            >
              <Search className="h-5 w-5" />
              KHÁM PHÁ NHÀ HÀNG
            </Button>
            <Button
              variant="outline"
              onClick={onNavigateToChatbot}
              className="bg-white/80 backdrop-blur-lg border-2 border-pink-300 hover:bg-pink-100 text-pink-700 rounded-2xl px-8 py-6 shadow-lg font-bold"
              style={{ boxShadow: "0 0 20px rgba(255,182,193,0.4)" }}
            >
              <MessageCircle className="h-5 w-5" />
              TRÒ CHUYỆN CÙNG AI
            </Button>
          </div>
        </div>

        {/* Featured Dishes */}
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-pink-800 font-bold">✨ MÓN ĂN NỔI BẬT ✨</h2>
            <p className="text-pink-600">Khám phá những món ăn đặc trưng của Việt Nam</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {featuredDishes.map((dish, idx) => (
              <Card
                key={idx}
                className="group overflow-hidden bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 hover:border-pink-300 rounded-3xl shadow-lg hover:shadow-2xl transition-all cursor-pointer"
                style={{ boxShadow: "0 0 25px rgba(255,182,193,0.3)" }}
              >
                <div className="relative h-48 overflow-hidden">
                  <ImageWithFallback
                    src={dish.image}
                    alt={dish.name}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                  />
                </div>
                <div className="p-5 space-y-2 pt-2">
                  <h3 className="text-pink-800">{dish.name}</h3>
                  <p className="text-gray-700 text-sm text-ju">{dish.description}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Features */}
        <div className="space-y-6">
          <div className="text-center">
            <h2 className="text-pink-800 font-bold">🌟 TÍNH NĂNG NỔI BẬT 🌟</h2>
            <p className="text-pink-600">Trải nghiệm đặt bàn nhà hàng hiện đại và tiện lợi</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, idx) => (
              <Card
                key={idx}
                className="bg-gradient-to-br from-pink-100/90 via-rose-100/90 to-fuchsia-100/90 backdrop-blur-xl border-2 border-pink-200 rounded-3xl p-6 shadow-lg hover:shadow-xl transition-all"
                style={{ boxShadow: "0 0 20px rgba(255,182,193,0.3)" }}
              >
                <div className="space-y-3">
                  <div
                    className="w-14 h-14 rounded-2xl bg-gradient-to-br from-pink-400 to-rose-400 flex items-center justify-center shadow-lg"
                    style={{ boxShadow: "0 0 20px rgba(255,182,193,0.5)" }}
                  >
                    <feature.icon className="h-7 w-7 text-white" />
                  </div>
                  <h3 className="text-pink-800">{feature.title}</h3>
                  <p className="text-gray-700 text-sm text-ju">{feature.description}</p>
                </div>
              </Card>
            ))}
          </div>
        </div>

        {/* Call to Action */}
        <Card
          className="bg-gradient-to-r from-pink-400 via-rose-400 to-fuchsia-400 border-2 border-pink-300 rounded-3xl p-8 md:p-12 text-center shadow-2xl"
          style={{ boxShadow: "0 0 40px rgba(255,182,193,0.5)" }}
        >
          <div className="space-y-4">
            <h2 className="text-white font-bold">ĐỪNG ĐỂ CÂU HỎI "HÔM NAY ĂN GÌ" LÀM KHÓ BẠN</h2>
            <p className="text-white/90 font-bold max-w-2xl mx-auto">
              Chấm dứt hàng giờ lướt web vô định. Hãy để trợ lý AI thấu hiểu khẩu vị và đưa bạn đến bàn tiệc hoàn hảo chỉ trong 30 giây.
            </p>
            <Button
              onClick={onNavigateToRestaurants}
              className= "bg-white/80 backdrop-blur-lg border-2 border-pink-300 hover:bg-pink-100 text-pink-700 rounded-2xl px-8 py-6 shadow-lg font-bold"
            >
              <Search className="h-5 w-5" />
              TÌM QUÁN NGAY
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
}
