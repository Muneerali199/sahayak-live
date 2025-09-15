"use client";

import * as React from "react";
import Link from "next/link";
import Image from "next/image";
import {
  ArrowRight,
  BrainCircuit,
  Languages,
  Paintbrush,
  BookOpenCheck,
  Sparkles,
  CalendarCheck,
  GitBranch,
  Github,
  Linkedin,
  Twitter,
  Code2,
  Cpu,
  Play,
  Star,
  Users,
  Zap,
  Heart,
  CheckCircle,
  Globe,
  BookOpen,
  PenTool,
  MessageCircle,
  Award,
  TrendingUp,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Logo } from "@/components/icons";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { useIsMobile } from "@/hooks/use-mobile";

// Enhanced animations with framer-motion-like behavior using CSS
const MotionDiv = ({ 
  children, 
  className = "", 
  delay = 0, 
  ...props 
}: { 
  children: React.ReactNode; 
  className?: string; 
  delay?: number;
  [key: string]: any;
}) => {
  const [isVisible, setIsVisible] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setTimeout(() => setIsVisible(true), delay * 100);
        }
      },
      { threshold: 0.1 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, [delay]);

  return (
    <div
      ref={ref}
      className={`transition-all duration-700 ${
        isVisible 
          ? 'opacity-100 translate-y-0' 
          : 'opacity-0 translate-y-8'
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export default function LandingPage() {
  const followerRef = React.useRef<HTMLDivElement>(null);
  const isMobile = useIsMobile();
  const [mousePosition, setMousePosition] = React.useState({ x: 0, y: 0 });

  React.useEffect(() => {
    if (isMobile) return;

    const handleMouseMove = (event: MouseEvent) => {
      setMousePosition({ x: event.clientX, y: event.clientY });
      if (followerRef.current) {
        const { clientX, clientY } = event;
        followerRef.current.style.transform = `translate(${clientX}px, ${clientY}px) translate(-50%, -50%)`;
      }
    };

    window.addEventListener("mousemove", handleMouseMove);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, [isMobile]);

  const features = [
    {
      icon: <Languages className="w-8 h-8" />,
      title: "Localized Content Generation",
      description: "Create stories and examples in Hindi, Marathi, and more from a simple prompt.",
      color: "from-blue-500 to-cyan-500",
    },
    {
      icon: <BookOpenCheck className="w-8 h-8" />,
      title: "Differentiated Materials", 
      description: "Generate multiple versions of a worksheet from a textbook photo for different grade levels.",
      color: "from-purple-500 to-pink-500",
    },
    {
      icon: <BrainCircuit className="w-8 h-8" />,
      title: "Instant Knowledge Base",
      description: "Get simple, clear explanations for complex student questions with voice or text.",
      color: "from-emerald-500 to-teal-500",
    },
    {
      icon: <Paintbrush className="w-8 h-8" />,
      title: "Visual Aid Design",
      description: "Describe a concept and get a simple visual aid you can draw on a blackboard.",
      color: "from-orange-500 to-red-500",
    },
    {
      icon: <CalendarCheck className="w-8 h-8" />,
      title: "Weekly Lesson Planner",
      description: "Automate the creation of structured weekly lesson plans for any topic and grade.",
      color: "from-indigo-500 to-purple-500",
    },
    {
      icon: <Sparkles className="w-8 h-8" />,
      title: "And much more...",
      description: "From audio assessments to on-the-fly game generation, Sahayak is your all-in-one assistant.",
      color: "from-yellow-500 to-orange-500",
    },
  ];

  const stats = [
    { value: "10K+", label: "Teachers Helped", icon: <Users className="w-6 h-6" /> },
    { value: "50K+", label: "Lessons Created", icon: <BookOpen className="w-6 h-6" /> },
    { value: "25+", label: "Languages Supported", icon: <Globe className="w-6 h-6" /> },
    { value: "99.9%", label: "Uptime", icon: <Shield className="w-6 h-6" /> },
  ];

  const techStack = [
    {
      name: 'Next.js',
      logo: (
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-gray-900 to-gray-700 flex items-center justify-center text-white font-bold">
          N
        </div>
      )
    },
    {
      name: 'React',
      logo: (
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 flex items-center justify-center text-white">
          <div className="w-8 h-8 border-2 border-current rounded-full relative">
            <div className="absolute inset-0 border border-current rounded-full transform rotate-45"></div>
            <div className="absolute inset-0 border border-current rounded-full transform -rotate-45"></div>
          </div>
        </div>
      )
    },
    {
      name: 'Tailwind CSS',
      logo: (
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white font-bold">
          T
        </div>
      )
    },
    {
      name: 'Firebase',
      logo: (
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-orange-500 to-yellow-500 flex items-center justify-center text-white">
          <div className="w-6 h-6 bg-current rounded transform rotate-12"></div>
        </div>
      )
    },
    {
      name: 'Google AI',
      logo: (
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-blue-500 flex items-center justify-center text-white">
          <Sparkles className="w-6 h-6" />
        </div>
      )
    },
    {
      name: 'Genkit',
      logo: (
        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-white">
          <GitBranch className="w-6 h-6" />
        </div>
      )
    }
  ];

  const teamMembers = [
    {
      name: "Stuti mishra",
      role: "Full Stack Developer",
      icon: <Code2 className="w-8 h-8" />,
      gradient: "from-blue-500 to-purple-500",
      social: {
        github: "https://github.com/Muneerali199",
        linkedin: "https://linkedin.com/in/muneer-ali",
        twitter: "https://twitter.com/Muneerali199"
      }
    },
    {
      name: "Amitesh",
      role: "Backend Developer",
      icon: <Cpu className="w-8 h-8" />,
      gradient: "from-emerald-500 to-teal-500",
      social: {
        github: "https://github.com/Mohammad-Ehshan/",
        linkedin: "https://linkedin.com/in/mohammad-ehshan-4362a0298/",
        twitter: "https://twitter.com"
      }
    },
    {
      name: "Amardeep",
      role: "AI Specialist",
      icon: <BrainCircuit className="w-8 h-8" />,
      gradient: "from-pink-500 to-orange-500",
      social: {
        github: "https://github.com/Stutyay",
        linkedin: "https://linkedin.com/in/stuti-gupta-256839293/",
        twitter: "https://twitter.com"
      }
    },
    {
      name: "kapil",
      role: "ui ux designer",
      icon: <BrainCircuit className="w-8 h-8" />,
      gradient: "from-pink-500 to-orange-500",
      social: {
        github: "https://github.com/Stutyay",
        linkedin: "https://linkedin.com/in/stuti-gupta-256839293/",
        twitter: "https://twitter.com"
      }
    },
     {
      name: "Ayush",
      role: "deploy manager",
      icon: <BrainCircuit className="w-8 h-8" />,
      gradient: "from-pink-500 to-orange-500",
      social: {
        github: "https://github.com/Stutyay",
        linkedin: "https://linkedin.com/in/stuti-gupta-256839293/",
        twitter: "https://twitter.com"
      }
     },
     {
      name: "Pratyush",
      role: "QA tester",
      icon: <BrainCircuit className="w-8 h-8" />,
      gradient: "from-pink-500 to-orange-500",
      social: {
        github: "https://github.com/Stutyay",
        linkedin: "https://linkedin.com/in/stuti-gupta-256839293/",
        twitter: "https://twitter.com"
      }
     }
  
  ];

  const testimonials = [
    {
      name: "Priya Sharma",
      role: "Primary School Teacher",
      content: "Sahayak has transformed how I prepare lessons. Creating Hindi content for my students is now effortless!",
      avatar: "https://images.unsplash.com/photo-1494790108755-2616b612b4c6?w=150&h=150&fit=crop&crop=face"
    },
    {
      name: "Rajesh Kumar",
      role: "Mathematics Teacher",
      content: "The visual aids and differentiated materials save me hours of preparation time. Absolutely game-changing!",
      avatar: "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=150&h=150&fit=crop&crop=face"
    },
    {
      name: "Anita Desai",
      role: "English Teacher",
      content: "Finally, an AI tool that understands the Indian classroom context. My students love the localized examples.",
      avatar: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&h=150&fit=crop&crop=face"
    }
  ];

  return (
    <>
      {!isMobile && (
        <div 
          ref={followerRef} 
          className="fixed w-8 h-8 rounded-full pointer-events-none z-50 transition-all duration-200 ease-out"
          style={{
            background: `radial-gradient(circle, hsl(var(--primary) / 0.3) 0%, transparent 70%)`,
            backdropFilter: 'blur(2px)',
          }}
        />
      )}
      
      <div className="flex flex-col min-h-screen bg-background text-foreground overflow-x-hidden">
        {/* Animated background */}
        <div className="fixed inset-0 -z-50">
          <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-primary/5 dark:to-primary/10"></div>
          <div className="absolute top-[-20%] left-[-20%] w-[60%] h-[60%] bg-gradient-to-r from-primary/20 to-purple-500/20 rounded-full filter blur-3xl animate-float" />
          <div className="absolute bottom-[-20%] right-[-20%] w-[60%] h-[60%] bg-gradient-to-r from-accent/20 to-pink-500/20 rounded-full filter blur-3xl animate-float" style={{ animationDelay: '2s' }} />
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[40%] h-[40%] bg-gradient-to-r from-blue-500/10 to-cyan-500/10 rounded-full filter blur-3xl animate-float" style={{ animationDelay: '4s' }} />
        </div>

        {/* Header */}
        <header className="sticky top-0 z-50 w-full border-b border-border/40 glass">
          <div className="container flex h-20 items-center justify-between">
            <MotionDiv className="flex items-center gap-3">
              <div className="relative">
                <Logo className="h-10 w-10 text-primary drop-shadow-lg" />
                <div className="absolute -inset-1 bg-gradient-to-r from-primary to-purple-500 rounded-full blur opacity-30 animate-pulse"></div>
              </div>
              <span className="text-2xl font-bold font-headline bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent">
                Sahayak Teacher
              </span>
            </MotionDiv>
            
            <nav className="flex items-center gap-4">
              <ThemeToggle />
              <Link href="/login" className="hidden sm:block">
                <Button variant="ghost" className="hover:bg-primary/10 transition-all duration-300">
                  Sign In
                </Button>
              </Link>
              <Link href="/login">
                <Button className="relative overflow-hidden bg-gradient-to-r from-primary to-purple-500 hover:from-primary/90 hover:to-purple-500/90 shadow-lg hover:shadow-primary/30 transition-all duration-300 transform hover:scale-105">
                  <span className="relative z-10">Get Started</span>
                  <ArrowRight className="ml-2 h-4 w-4 relative z-10" />
                  <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 opacity-0 hover:opacity-100 transition-opacity duration-300"></div>
                </Button>
              </Link>
            </nav>
          </div>
        </header>

        <main className="flex-1">
          {/* Hero Section */}
          <section className="relative py-24 md:py-32 lg:py-40 overflow-hidden">
            <div className="container relative z-10">
              <div className="text-center max-w-4xl mx-auto">
                <MotionDiv delay={0}>
                  <Badge className="mb-6 bg-gradient-to-r from-primary/20 to-purple-500/20 text-primary border-primary/30 shadow-lg hover:shadow-primary/20 transition-all duration-300">
                    <Sparkles className="w-4 h-4 mr-2" />
                    Hackathon Submission - Built with ❤️
                  </Badge>
                </MotionDiv>
                
                <MotionDiv delay={1}>
                  <h1 className="text-5xl md:text-7xl lg:text-8xl font-extrabold tracking-tight font-headline mb-8">
                    <span className="bg-gradient-to-r from-gray-900 via-gray-600 to-gray-900 dark:from-white dark:via-gray-300 dark:to-white bg-clip-text text-transparent">
                      Your AI-Powered
                    </span>
                    <br />
                    <span className="bg-gradient-to-r from-primary via-purple-500 to-pink-500 bg-clip-text text-transparent animate-gradient">
                      Teaching Assistant
                    </span>
                  </h1>
                </MotionDiv>
                
                <MotionDiv delay={2}>
                  <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-12 leading-relaxed">
                    Spend less time on prep and more time on what matters most—teaching. 
                    <span className="text-primary font-semibold"> Sahayak</span> helps you with lesson plans, materials, and creative ideas, all in your local language.
                  </p>
                </MotionDiv>
                
                <MotionDiv delay={3} className="flex flex-col sm:flex-row gap-4 justify-center items-center">
                  <Link href="/login">
                    <Button 
                      size="lg" 
                      className="relative group overflow-hidden bg-gradient-to-r from-primary to-purple-500 hover:from-primary/90 hover:to-purple-500/90 shadow-2xl hover:shadow-primary/30 transition-all duration-300 transform hover:scale-105 text-lg px-8 py-6"
                    >
                      <span className="relative z-10 flex items-center">
                        Start For Free
                        <ArrowRight className="ml-2 h-5 w-5 group-hover:translate-x-1 transition-transform" />
                      </span>
                      <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    </Button>
                  </Link>
                  
                  <Button 
                    variant="outline" 
                    size="lg" 
                    className="border-primary/30 hover:border-primary text-primary hover:bg-primary/5 transition-all duration-300 text-lg px-8 py-6 backdrop-blur-sm"
                  >
                    <Play className="mr-2 h-5 w-5" />
                    Watch Demo
                  </Button>
                </MotionDiv>

                {/* Stats */}
                <MotionDiv delay={4} className="mt-20">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
                    {stats.map((stat, index) => (
                      <div key={index} className="text-center">
                        <div className="flex justify-center mb-2">
                          <div className="p-3 rounded-full bg-gradient-to-r from-primary/20 to-purple-500/20">
                            {stat.icon}
                          </div>
                        </div>
                        <div className="text-3xl md:text-4xl font-bold font-headline text-primary">
                          {stat.value}
                        </div>
                        <div className="text-sm text-muted-foreground">
                          {stat.label}
                        </div>
                      </div>
                    ))}
                  </div>
                </MotionDiv>
              </div>
            </div>
            
            {/* Floating elements */}
            <div className="absolute top-20 left-10 w-4 h-4 bg-primary/30 rounded-full animate-sparkle" style={{ animationDelay: '0s' }}></div>
            <div className="absolute top-40 right-20 w-3 h-3 bg-purple-500/30 rounded-full animate-sparkle" style={{ animationDelay: '1s' }}></div>
            <div className="absolute bottom-20 left-20 w-5 h-5 bg-pink-500/30 rounded-full animate-sparkle" style={{ animationDelay: '2s' }}></div>
            <div className="absolute bottom-40 right-10 w-2 h-2 bg-cyan-500/30 rounded-full animate-sparkle" style={{ animationDelay: '0.5s' }}></div>
          </section>

          {/* Features Section */}
          <section className="py-24 md:py-32 relative">
            <div className="container">
              <MotionDiv className="text-center mb-20">
                <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold font-headline mb-6">
                  <span className="bg-gradient-to-r from-gray-900 to-gray-600 dark:from-white dark:to-gray-300 bg-clip-text text-transparent">
                    Everything a Teacher
                  </span>
                  <br />
                  <span className="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
                    Needs
                  </span>
                </h2>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                  From planning to assessment, Sahayak has you covered with AI-powered tools designed for educators.
                </p>
              </MotionDiv>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                {features.map((feature, index) => (
                  <MotionDiv key={index} delay={index} className="group">
                    <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-white/50 to-white/30 dark:from-gray-900/50 dark:to-gray-800/30 backdrop-blur-sm shadow-xl hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 hover:scale-105">
                      <div className={`absolute inset-0 bg-gradient-to-br ${feature.color} opacity-0 group-hover:opacity-10 transition-opacity duration-500`}></div>
                      <CardHeader className="relative z-10">
                        <div className={`w-16 h-16 rounded-2xl bg-gradient-to-br ${feature.color} p-4 text-white mb-4 shadow-lg group-hover:scale-110 transition-transform duration-300`}>
                          {feature.icon}
                        </div>
                        <CardTitle className="text-xl font-bold font-headline group-hover:text-primary transition-colors">
                          {feature.title}
                        </CardTitle>
                      </CardHeader>
                      <CardContent className="relative z-10">
                        <CardDescription className="text-muted-foreground text-base leading-relaxed">
                          {feature.description}
                        </CardDescription>
                      </CardContent>
                      <div className="absolute top-4 right-4 w-8 h-8 rounded-full bg-gradient-to-br from-white/20 to-white/10 group-hover:scale-110 transition-transform duration-300"></div>
                    </Card>
                  </MotionDiv>
                ))}
              </div>
            </div>
          </section>

          {/* Tech Stack Section */}
          <section className="py-24 md:py-32 bg-gradient-to-br from-secondary/30 to-background">
            <div className="container">
              <MotionDiv className="text-center mb-20">
                <h2 className="text-4xl md:text-5xl font-bold font-headline mb-6">
                  Powered by 
                  <span className="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent ml-3">
                    Cutting-Edge Tech
                  </span>
                </h2>
                <p className="text-xl text-muted-foreground max-w-3xl mx-auto">
                  Built with the most advanced tools and technologies to deliver a reliable, fast, and intelligent experience.
                </p>
              </MotionDiv>
              
              <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-8">
                {techStack.map((tech, index) => (
                  <MotionDiv 
                    key={index}
                    delay={index}
                    className="group flex flex-col items-center text-center hover:transform hover:scale-110 transition-all duration-300"
                  >
                    <div className="mb-4 group-hover:rotate-12 transition-transform duration-300">
                      {tech.logo}
                    </div>
                    <span className="font-semibold text-muted-foreground group-hover:text-primary transition-colors">
                      {tech.name}
                    </span>
                  </MotionDiv>
                ))}
              </div>
            </div>
          </section>

          {/* Testimonials Section */}
          <section className="py-24 md:py-32">
            <div className="container">
              <MotionDiv className="text-center mb-20">
                <h2 className="text-4xl md:text-5xl font-bold font-headline mb-6">
                  Loved by 
                  <span className="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
                    Teachers
                  </span>
                </h2>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                  See what educators across India are saying about Sahayak Teacher.
                </p>
              </MotionDiv>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {testimonials.map((testimonial, index) => (
                  <MotionDiv key={index} delay={index}>
                    <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-white/80 to-white/40 dark:from-gray-900/80 dark:to-gray-800/40 backdrop-blur-sm shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1">
                      <CardContent className="p-8">
                        <div className="flex items-center mb-6">
                          {[...Array(5)].map((_, i) => (
                            <Star key={i} className="w-5 h-5 text-yellow-400 fill-current" />
                          ))}
                        </div>
                        <blockquote className="text-lg mb-6 leading-relaxed">
                          "{testimonial.content}"
                        </blockquote>
                        <div className="flex items-center">
                          <Image
                            src={testimonial.avatar}
                            alt={testimonial.name}
                            width={50}
                            height={50}
                            className="rounded-full mr-4"
                          />
                          <div>
                            <div className="font-semibold">{testimonial.name}</div>
                            <div className="text-sm text-muted-foreground">{testimonial.role}</div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </MotionDiv>
                ))}
              </div>
            </div>
          </section>

          {/* Indian Classroom Section */}
          <section className="py-24 md:py-32 bg-gradient-to-br from-primary/5 to-purple-500/5">
            <div className="container">
              <div className="grid md:grid-cols-2 gap-16 items-center">
                <MotionDiv className="order-2 md:order-1">
                  <Badge className="mb-6 bg-gradient-to-r from-primary/20 to-purple-500/20 text-primary border-primary/30">
                    <Globe className="w-4 h-4 mr-2" />
                    Made for India
                  </Badge>
                  <h2 className="text-4xl md:text-5xl font-bold font-headline mb-6">
                    Built for the 
                    <span className="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
                      {" "}Indian Classroom
                    </span>
                  </h2>
                  <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
                    Sahayak understands the unique needs of teachers in India. It generates hyper-local content, 
                    works with multiple Indian languages, and creates materials that are culturally relevant and easy to use in your classroom.
                  </p>
                  
                  <div className="space-y-4 mb-8">
                    {[
                      "25+ Indian languages supported",
                      "Culturally relevant content",
                      "Local curriculum aligned",
                      "Works offline when needed"
                    ].map((feature, index) => (
                      <div key={index} className="flex items-center">
                        <CheckCircle className="w-5 h-5 text-green-500 mr-3" />
                        <span className="text-muted-foreground">{feature}</span>
                      </div>
                    ))}
                  </div>
                  
                  <Link href="/login">
                    <Button size="lg" variant="outline" className="border-primary text-primary hover:bg-primary/10 transition-all duration-300 transform hover:scale-105">
                      See it in Action
                      <ArrowRight className="ml-2 h-5 w-5" />
                    </Button>
                  </Link>
                </MotionDiv>
                
                <MotionDiv delay={2} className="order-1 md:order-2 relative">
                  <div className="absolute -inset-4 bg-gradient-to-br from-primary to-purple-500 rounded-3xl opacity-20 blur-xl"></div>
                  <div className="relative p-2 bg-gradient-to-br from-primary/80 via-primary/40 to-background dark:from-primary/60 dark:via-primary/30 rounded-3xl shadow-2xl overflow-hidden">
                    <Image
                      src="https://images.unsplash.com/photo-1588072432836-e10032774350?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1200&q=80"
                      alt="Teacher in an Indian classroom"
                      width={600}
                      height={450}
                      className="rounded-2xl transform hover:scale-105 transition-transform duration-500"
                      priority
                    />
                  </div>
                  <div className="absolute top-8 right-8 bg-white/90 dark:bg-gray-900/90 backdrop-blur-sm rounded-xl p-4 shadow-lg">
                    <div className="flex items-center gap-2 text-sm font-semibold">
                      <TrendingUp className="w-4 h-4 text-green-500" />
                      <span>98% Teacher Satisfaction</span>
                    </div>
                  </div>
                </MotionDiv>
              </div>
            </div>
          </section>

          {/* Team Section */}
          <section className="py-24 md:py-32">
            <div className="container">
              <MotionDiv className="text-center mb-20">
                <h2 className="text-4xl md:text-5xl font-bold font-headline mb-6">
                  Meet Our 
                  <span className="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
                    Team
                  </span>
                </h2>
                <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                  The brilliant minds behind Sahayak Teacher, passionate about transforming education through AI.
                </p>
              </MotionDiv>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {teamMembers.map((member, index) => (
                  <MotionDiv key={index} delay={index} className="group">
                    <Card className="relative overflow-hidden border-0 bg-gradient-to-br from-white/80 to-white/40 dark:from-gray-900/80 dark:to-gray-800/40 backdrop-blur-sm shadow-xl hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 text-center">
                      <div className={`absolute inset-0 bg-gradient-to-br ${member.gradient} opacity-0 group-hover:opacity-10 transition-opacity duration-500`}></div>
                      
                      <CardContent className="p-8 relative z-10">
                        <div className={`w-32 h-32 mx-auto mb-6 rounded-full bg-gradient-to-br ${member.gradient} p-8 shadow-xl group-hover:scale-110 transition-transform duration-300 flex items-center justify-center text-white`}>
                          {member.icon}
                        </div>
                        
                        <h3 className="text-2xl font-bold font-headline mb-2 group-hover:text-primary transition-colors">
                          {member.name}
                        </h3>
                        
                        <Badge className="mb-6 bg-gradient-to-r from-primary/20 to-purple-500/20 text-primary border-primary/30">
                          {member.role}
                        </Badge>
                        
                        <div className="flex justify-center gap-4">
                          <Link href={member.social.github} target="_blank" className="text-muted-foreground hover:text-primary transition-all duration-300 hover:scale-110">
                            <Github className="w-6 h-6" />
                          </Link>
                          <Link href={member.social.linkedin} target="_blank" className="text-muted-foreground hover:text-primary transition-all duration-300 hover:scale-110">
                            <Linkedin className="w-6 h-6" />
                          </Link>
                          <Link href={member.social.twitter} target="_blank" className="text-muted-foreground hover:text-primary transition-all duration-300 hover:scale-110">
                            <Twitter className="w-6 h-6" />
                          </Link>
                        </div>
                      </CardContent>
                    </Card>
                  </MotionDiv>
                ))}
              </div>
            </div>
          </section>

          {/* CTA Section */}
          <section className="py-24 md:py-32 relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-primary/10 to-purple-500/10"></div>
            <div className="container relative z-10 text-center">
              <MotionDiv>
                <h2 className="text-4xl md:text-5xl lg:text-6xl font-bold font-headline mb-6">
                  Ready to Transform Your 
                  <span className="bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
                    {" "}Teaching?
                  </span>
                </h2>
                <p className="text-xl md:text-2xl text-muted-foreground max-w-3xl mx-auto mb-12">
                  Join thousands of teachers who are already saving time and creating better learning experiences with Sahayak.
                </p>
                
                <div className="flex flex-col sm:flex-row gap-6 justify-center items-center">
                  <Link href="/login">
                    <Button 
                      size="lg" 
                      className="relative group overflow-hidden bg-gradient-to-r from-primary to-purple-500 hover:from-primary/90 hover:to-purple-500/90 shadow-2xl hover:shadow-primary/30 transition-all duration-300 transform hover:scale-105 text-xl px-12 py-8"
                    >
                      <span className="relative z-10 flex items-center">
                        Get Started Free
                        <Zap className="ml-2 h-6 w-6 group-hover:rotate-12 transition-transform" />
                      </span>
                      <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                    </Button>
                  </Link>
                  
                  <div className="text-center">
                    <p className="text-sm text-muted-foreground">
                      No credit card required • 14-day free trial
                    </p>
                  </div>
                </div>
              </MotionDiv>
            </div>
          </section>
        </main>

        {/* Footer */}
        <footer className="border-t border-border/40 bg-gradient-to-br from-secondary/30 to-background">
          <div className="container py-16">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
              <div className="md:col-span-2">
                <div className="flex items-center gap-3 mb-6">
                  <div className="relative">
                    <Logo className="h-12 w-12 text-primary" />
                    <div className="absolute -inset-1 bg-gradient-to-r from-primary to-purple-500 rounded-full blur opacity-30"></div>
                  </div>
                  <span className="text-2xl font-bold font-headline bg-gradient-to-r from-primary to-purple-500 bg-clip-text text-transparent">
                    Sahayak Teacher
                  </span>
                </div>
                <p className="text-muted-foreground mb-6 max-w-md">
                  Empowering teachers across India with AI-powered tools for creating engaging, localized educational content.
                </p>
                <div className="flex items-center gap-4">
                  <ThemeToggle />
                  <Link href="/login">
                    <Button size="sm" className="bg-gradient-to-r from-primary to-purple-500 shadow-md hover:shadow-primary/30">
                      Get Started
                    </Button>
                  </Link>
                </div>
              </div>
              
              <div>
                <h3 className="font-semibold mb-4">Product</h3>
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li><Link href="#" className="hover:text-primary transition-colors">Features</Link></li>
                  <li><Link href="#" className="hover:text-primary transition-colors">Pricing</Link></li>
                  <li><Link href="#" className="hover:text-primary transition-colors">API</Link></li>
                  <li><Link href="#" className="hover:text-primary transition-colors">Documentation</Link></li>
                </ul>
              </div>
              
              <div>
                <h3 className="font-semibold mb-4">Company</h3>
                <ul className="space-y-3 text-sm text-muted-foreground">
                  <li><Link href="#" className="hover:text-primary transition-colors">About</Link></li>
                  <li><Link href="#" className="hover:text-primary transition-colors">Blog</Link></li>
                  <li><Link href="#" className="hover:text-primary transition-colors">Careers</Link></li>
                  <li><Link href="#" className="hover:text-primary transition-colors">Contact</Link></li>
                </ul>
              </div>
            </div>
            
            <div className="mt-12 pt-8 border-t border-border/20 flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="text-sm text-muted-foreground">
                © 2024 Sahayak Teacher. Built with <Heart className="w-4 h-4 text-red-500 inline" /> by Team 1-blitz!
              </div>
              
              <div className="flex gap-6 text-sm text-muted-foreground">
                <Link href="#" className="hover:text-primary transition-colors">Privacy Policy</Link>
                <Link href="#" className="hover:text-primary transition-colors">Terms of Service</Link>
                <Link href="#" className="hover:text-primary transition-colors">Cookie Policy</Link>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
}
