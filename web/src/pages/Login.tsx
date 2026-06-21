import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";
import { z } from "zod";
import { useAuth } from "../stores/auth";

const loginSchema = z.object({
  telegram_id: z.coerce.number({ message: "Telegram ID raqam bo'lishi kerak" }),
  token: z.string().min(1, "Token talab qilinadi"),
});

type LoginForm = z.infer<typeof loginSchema>;

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginForm) => {
    setError("");
    setLoading(true);
    try {
      await login(data.telegram_id, data.token);
      navigate("/");
    } catch {
      setError("Kirish muvaffaqiyatsiz. Telegram ID yoki tokenni tekshiring.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-accent-600 shadow-lg shadow-accent-600/20">
            <span className="text-2xl font-bold text-white">S</span>
          </div>
          <h1 className="text-2xl font-bold text-surface-900">SecAdmin</h1>
          <p className="mt-1 text-sm text-surface-500">Xavfsizlik boshqaruv paneli</p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="card space-y-4">
          {error && (
            <div className="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700 ring-1 ring-red-600/20">
              {error}
            </div>
          )}

          <div>
            <label className="mb-1 block text-sm font-medium text-surface-700">
              Telegram ID
            </label>
            <input
              {...register("telegram_id")}
              className="input"
              placeholder="123456789"
            />
            {errors.telegram_id && (
              <p className="mt-1 text-xs text-red-600">{errors.telegram_id.message}</p>
            )}
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-surface-700">
              Token
            </label>
            <input
              {...register("token")}
              className="input"
              type="password"
              placeholder="Maxfiy token"
            />
            {errors.token && (
              <p className="mt-1 text-xs text-red-600">{errors.token.message}</p>
            )}
          </div>

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? "Kirish..." : "Kirish"}
          </button>
        </form>
      </div>
    </div>
  );
}
