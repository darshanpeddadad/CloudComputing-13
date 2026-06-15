import React, { useEffect, useState } from "react";
import { Link } from "react-router";
import { Button } from "../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Calendar, Users, Ticket, Search, TrendingUp, Shield, Sparkles, ArrowRight, Clock, MapPin } from "lucide-react";
import axios from "axios";
import { baseUrl } from "../routes";

const HomePage = () => {
  const [upcomingEvents, setUpcomingEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchUpcomingEvents = async () => {
      try {
        const res = await axios.get(`${baseUrl}events/`);
        const payload = res.data;
        let items = [];
        if (Array.isArray(payload)) {
          items = payload;
        } else if (Array.isArray(payload?.data)) {
          items = payload.data;
        } else if (Array.isArray(payload?.data?.items)) {
          items = payload.data.items;
        } else if (Array.isArray(payload?.items)) {
          items = payload.items;
        }
        setUpcomingEvents(items.slice(0, 3));
      } catch (error) {
        console.error("Failed to fetch events:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchUpcomingEvents();
  }, []);

  const features = [
    {
      icon: Calendar,
      title: "Easy Event Creation",
      description: "Create and manage events effortlessly with our intuitive interface"
    },
    {
      icon: Ticket,
      title: "Smart Ticketing",
      description: "Seamless ticket booking and management system for attendees"
    },
    {
      icon: Users,
      title: "Community Driven",
      description: "Connect with like-minded people and build your network"
    },
    {
      icon: Search,
      title: "Discover Events",
      description: "Find events that match your interests with powerful search"
    },
    {
      icon: TrendingUp,
      title: "Analytics & Insights",
      description: "Track event performance with detailed analytics"
    },
    {
      icon: Shield,
      title: "Secure & Reliable",
      description: "Your data is protected with enterprise-grade security"
    }
  ];

  const steps = [
    {
      number: "01",
      title: "Browse Events",
      description: "Explore a wide variety of events happening around you"
    },
    {
      number: "02",
      title: "Book Tickets",
      description: "Secure your spot with our easy booking process"
    },
    {
      number: "03",
      title: "Enjoy Experience",
      description: "Attend events and create memorable experiences"
    }
  ];

  return (
    <div className="min-h-screen bg-background">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-50 via-white to-sky-50 dark:from-blue-950/30 dark:via-background dark:to-sky-950/30">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(59,130,246,0.15),transparent_50%),radial-gradient(circle_at_70%_80%,rgba(14,165,233,0.12),transparent_50%)]" />
        <div className="container mx-auto px-4 py-16 md:py-24 relative">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/90 dark:bg-card/90 backdrop-blur-sm border border-primary/20 text-primary text-sm font-medium mb-4 shadow-lg">
              <Sparkles className="w-4 h-4" />
              <span>Welcome to FuldaNexus</span>
            </div>
            
            <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold tracking-tight">
              Discover Amazing{" "}
              <span className="bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                Events
              </span>{" "}
              for <br></br>Hochschule Fulda
            </h1>
            
            <p className="text-lg md:text-xl text-foreground/80 max-w-2xl mx-auto">
              Join thousands of event enthusiasts. Create, discover, and attend events that matter to you.
            </p>
            
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
              <Link to="/events">
                <Button size="lg" className="w-full sm:w-auto shadow-lg hover:shadow-2xl hover:scale-105 transition-all duration-300 group">
                  Explore Events
                  <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                </Button>
              </Link>
              <Link to="/register">
                <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/80 dark:bg-card/80 backdrop-blur-sm hover:bg-primary/5 hover:text-primary hover:border-primary/50 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300">
                  Get Started Free
                </Button>
              </Link>
            </div>

            {/* Stats */}
            {/* <div className="grid grid-cols-3 gap-8 pt-12 max-w-2xl mx-auto">
              <div className="space-y-2 p-4 rounded-xl bg-white/60 dark:bg-card/60 backdrop-blur-sm border border-primary/10">
                <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">500+</div>
                <div className="text-sm font-medium text-foreground/70">Events</div>
              </div>
              <div className="space-y-2 p-4 rounded-xl bg-white/60 dark:bg-card/60 backdrop-blur-sm border border-secondary/10">
                <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-secondary to-accent bg-clip-text text-transparent">10K+</div>
                <div className="text-sm font-medium text-foreground/70">Attendees</div>
              </div>
              <div className="space-y-2 p-4 rounded-xl bg-white/60 dark:bg-card/60 backdrop-blur-sm border border-accent/10">
                <div className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-accent to-primary bg-clip-text text-transparent">50+</div>
                <div className="text-sm font-medium text-foreground/70">Organizers</div>
              </div>
            </div> */}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gradient-to-b from-background to-muted/50">
        <div className="container mx-auto px-4">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Why Choose FuldaNexus?
            </h2>
            <p className="text-lg text-muted-foreground">
              Everything you need to create, manage, and attend amazing events
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              const colors = [
                { bg: "bg-primary/10", icon: "text-primary", border: "hover:border-primary/50" },
                { bg: "bg-secondary/10", icon: "text-secondary", border: "hover:border-secondary/50" },
                { bg: "bg-accent/10", icon: "text-accent", border: "hover:border-accent/50" },
                { bg: "bg-primary/10", icon: "text-primary", border: "hover:border-primary/50" },
                { bg: "bg-secondary/10", icon: "text-secondary", border: "hover:border-secondary/50" },
                { bg: "bg-accent/10", icon: "text-accent", border: "hover:border-accent/50" }
              ];
              const color = colors[index];
              return (
                <Card key={index} className={`border-border ${color.border} transition-all hover:shadow-xl hover:scale-[1.02]`}>
                  <CardHeader>
                    <div className={`w-14 h-14 rounded-xl ${color.bg} flex items-center justify-center mb-4 shadow-sm`}>
                      <Icon className={`w-7 h-7 ${color.icon}`} />
                    </div>
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                    <CardDescription className="text-base">
                      {feature.description}
                    </CardDescription>
                  </CardHeader>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-20 bg-gradient-to-br from-secondary/10 via-background to-primary/10">
        <div className="container mx-auto px-4">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-secondary to-accent bg-clip-text text-transparent">
              How It Works
            </h2>
            <p className="text-lg text-muted-foreground">
              Get started in three simple steps
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 max-w-5xl mx-auto">
            {steps.map((step, index) => {
              const gradients = [
                "from-primary via-secondary to-primary",
                "from-secondary via-accent to-secondary",
                "from-accent via-primary to-accent"
              ];
              return (
                <div key={index} className="relative">
                  <div className="text-center space-y-4">
                    <div className={`w-24 h-24 mx-auto rounded-2xl bg-gradient-to-br ${gradients[index]} flex items-center justify-center text-white text-3xl font-bold shadow-xl hover:scale-110 transition-transform`}>
                      {step.number}
                    </div>
                    <h3 className="text-xl font-bold">{step.title}</h3>
                    <p className="text-muted-foreground">{step.description}</p>
                  </div>
                  {index < steps.length - 1 && (
                    <div className={`hidden md:block absolute top-12 left-[60%] w-[80%] h-1 bg-gradient-to-r ${gradients[index]} opacity-30 rounded-full`} />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Upcoming Events Preview */}
      <section className="py-20 bg-gradient-to-b from-background to-accent/10">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between mb-12 gap-4">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold mb-2 bg-gradient-to-r from-accent to-primary bg-clip-text text-transparent">
                Upcoming Events
              </h2>
              <p className="text-lg text-muted-foreground">
                Don't miss out on these exciting events
              </p>
            </div>
            <Link to="/events">
              <Button variant="outline" className="shadow-md hover:shadow-lg hover:bg-primary/5 hover:text-primary hover:border-primary/50 hover:scale-105 transition-all duration-300">
                View All
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="inline-block animate-spin rounded-full h-10 w-10 border-4 border-primary border-t-transparent"></div>
            </div>
          ) : upcomingEvents.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {upcomingEvents.map((event, idx) => {
                const borderColors = ["border-primary/30", "border-secondary/30", "border-accent/30"];
                return (
                  <Link key={event.id} to={`/events/${event.id}`}>
                    <Card className={`overflow-hidden hover:shadow-2xl transition-all hover:scale-[1.03] cursor-pointer h-full ${borderColors[idx % 3]} border-2`}>
                      {event.image_url && (
                        <div className="aspect-video overflow-hidden relative">
                          <img
                            src={event.image_url}
                            alt={event.title}
                            className="w-full h-full object-cover hover:scale-110 transition-transform duration-300"
                          />
                          <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent" />
                        </div>
                      )}
                      <CardHeader>
                        <CardTitle className="text-xl line-clamp-2">{event.title}</CardTitle>
                        <CardDescription className="space-y-2">
                          <div className="flex items-center gap-2 text-sm">
                            <Clock className="w-4 h-4 text-primary" />
                            <span>{new Date(event.start_date).toLocaleDateString()}</span>
                          </div>
                          {event.location && (
                            <div className="flex items-center gap-2 text-sm">
                              <MapPin className="w-4 h-4 text-secondary" />
                              <span className="line-clamp-1">{event.location}</span>
                            </div>
                          )}
                        </CardDescription>
                      </CardHeader>
                    </Card>
                  </Link>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">No upcoming events at the moment</p>
            </div>
          )}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-br from-primary/15 via-secondary/10 to-accent/15">
        <div className="container mx-auto px-4">
          <Card className="bg-gradient-to-br from-blue-50 via-sky-50 to-cyan-50 dark:from-blue-950/20 dark:via-sky-950/15 dark:to-cyan-950/20 border-primary/30 border-2 shadow-2xl overflow-hidden relative">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.15),transparent_70%)]" />
            <CardContent className="py-20 text-center space-y-6 relative">
              <h2 className="text-3xl md:text-5xl font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                Ready to Get Started?
              </h2>
              <p className="text-lg text-foreground/80 max-w-2xl mx-auto">
                Join our community today and start creating or attending amazing events
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-6">
                <Link to="/register">
                  <Button size="lg" className="w-full sm:w-auto shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300 group">
                    Create Account
                    <ArrowRight className="w-4 h-4 ml-2 group-hover:translate-x-1 transition-transform" />
                  </Button>
                </Link>
                <Link to="/events">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto bg-white/80 dark:bg-card/80 backdrop-blur-sm hover:bg-primary/5 hover:text-primary hover:border-primary/50 shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300">
                    Browse Events
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t-2 border-primary/20 py-12 bg-gradient-to-b from-background to-muted/50">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="space-y-4">
              <h3 className="text-2xl font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                FuldaNexus
              </h3>
              <p className="text-sm text-muted-foreground">
                Your gateway to amazing events and unforgettable experiences.
              </p>
            </div>
            
            <div>
              <h4 className="font-bold mb-4 text-primary">Platform</h4>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li><Link to="/events" className="hover:text-primary transition-colors flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                  Browse Events
                </Link></li>
                <li><Link to="/events/create" className="hover:text-secondary transition-colors flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                  Create Event
                </Link></li>
                <li><Link to="/about" className="hover:text-accent transition-colors flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent"></span>
                  About Us
                </Link></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-bold mb-4 text-secondary">Support</h4>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li><Link to="/contact" className="hover:text-primary transition-colors flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                  Contact
                </Link></li>
                <li><a href="#" className="hover:text-secondary transition-colors flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                  Help Center
                </a></li>
                <li><a href="#" className="hover:text-accent transition-colors flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent"></span>
                  FAQ
                </a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-bold mb-4 text-accent">Legal</h4>
              <ul className="space-y-3 text-sm text-muted-foreground">
                <li><a href="#" className="hover:text-primary transition-colors flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary"></span>
                  Privacy Policy
                </a></li>
                <li><a href="#" className="hover:text-secondary transition-colors flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                  Terms of Service
                </a></li>
                <li><a href="#" className="hover:text-accent transition-colors flex items-center gap-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-accent"></span>
                  Cookie Policy
                </a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-primary/20 mt-12 pt-8 text-center text-sm text-muted-foreground">
            <p>&copy; {new Date().getFullYear()} FuldaNexus. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default HomePage;
