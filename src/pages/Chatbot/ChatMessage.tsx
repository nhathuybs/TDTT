import { MapPin, Star, User } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { Avatar, AvatarFallback } from "../../components/ui/avatar";
import { Card } from "../../components/ui/card";
import { ImageWithFallback } from "../../components/figma/ImageWithFallback";

export interface ChatRecommendationRestaurant {
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

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  recommendations?: ChatRecommendationRestaurant[];
}

export function ChatMessage({ role, content, recommendations }: ChatMessageProps) {
  const isUser = role === "user";
  const navigate = useNavigate();

  return (
    <div
      className={`flex gap-4 p-6 ${
        isUser
          ? "bg-transparent"
          : "bg-gradient-to-r from-pink-200/70 via-rose-200/70 to-fuchsia-200/70 backdrop-blur-md border-2 border-pink-300 rounded-3xl my-2 mx-4 shadow-lg"
      }`}
      style={
        !isUser
          ? {
              boxShadow: "0 0 25px rgba(255,182,193,0.3), inset 0 0 20px rgba(255,255,255,0.3)",
            }
          : {}
      }
    >
      <Avatar className="h-10 w-10 flex-shrink-0 shadow-xl border-2 border-pink-300">
        <AvatarFallback
          className={
            isUser
              ? "bg-gradient-to-br from-pink-300 to-rose-400 shadow-lg"
              : "bg-gradient-to-br from-pink-400 via-rose-400 to-fuchsia-400 shadow-lg"
          }
          style={{
            boxShadow: "0 0 18px rgba(255,182,193,0.5)",
          }}
        >
          {isUser ? (
            <User className="h-5 w-5 text-white drop-shadow-[0_0_4px_rgba(255,255,255,0.8)]" />
          ) : (
            <span className="text-xl drop-shadow-[0_0_8px_rgba(255,255,255,0.8)]">🍜</span>
          )}
        </AvatarFallback>
      </Avatar>

      <div className="flex-1 space-y-2 overflow-hidden">
        <div className="text-gray-800 whitespace-pre-wrap break-words text-justify">{content}</div>

        {!isUser && recommendations && recommendations.length > 0 && (
          <div className="pt-2 grid grid-cols-1 sm:grid-cols-2 gap-3">
            {recommendations.map((r) => {
              const rating = typeof r.rating === "number" ? r.rating : 0;
              const reviewCount = typeof r.reviewCount === "number" ? r.reviewCount : 0;
              const priceLevel = typeof r.priceLevel === "number" ? r.priceLevel : 2;

              return (
                <Card
                  key={r.id}
                  className="cursor-pointer overflow-hidden bg-white/80 backdrop-blur-md border border-pink-200 hover:border-pink-300 rounded-2xl shadow-sm hover:shadow-md transition"
                  onClick={() => navigate(`/restaurants/${r.id}`)}
                >
                  <div className="flex gap-3 p-3">
                    <ImageWithFallback
                      src={r.image || ""}
                      alt={r.name}
                      className="w-16 h-16 rounded-xl object-cover flex-shrink-0 border border-pink-200 bg-white"
                    />

                    <div className="min-w-0 flex-1">
                      <div className="text-gray-900 font-medium truncate">{r.name}</div>
                      {r.cuisine && <div className="text-xs text-pink-600 truncate">{r.cuisine}</div>}

                      <div className="mt-1 flex items-center gap-2 text-xs text-gray-700">
                        <div className="flex items-center gap-1">
                          <Star className="h-3.5 w-3.5 fill-yellow-400 text-yellow-400" />
                          <span className="tabular-nums">{rating.toFixed(1)}</span>
                          <span className="text-gray-500">({reviewCount})</span>
                        </div>
                        <span className="text-gray-400">•</span>
                        <span className="text-pink-700">{Array(priceLevel).fill("$").join("")}</span>
                      </div>

                      {r.address && (
                        <div className="mt-2 flex items-start gap-1 text-xs text-gray-600">
                          <MapPin className="h-3.5 w-3.5 text-pink-500 mt-0.5 flex-shrink-0" />
                          {r.googleMapsUrl ? (
                            <a
                              href={r.googleMapsUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="underline underline-offset-4 decoration-pink-300 hover:decoration-pink-500 hover:text-pink-700 transition-colors line-clamp-2"
                              onClick={(e) => e.stopPropagation()}
                              title="Mở Google Maps"
                            >
                              {r.address}
                            </a>
                          ) : (
                            <span className="line-clamp-2">{r.address}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
