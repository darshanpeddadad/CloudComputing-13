import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Link } from "react-router";
import { Users, Target, Zap, Shield, Heart, Sparkles, ArrowRight, CheckCircle2 } from "lucide-react";

const About = () => {
  const benefits = [
    "Simplified, efficient event management from creation to attendance",
    "Diverse event options for conferences, workshops, and social gatherings",
    "User-friendly interface for smooth navigation and booking",
    "Transparency and trust in every aspect of the event process",
    "Event organizers enjoy an efficient listing and management process",
    "Secure ticketing system with QR code verification"
  ];

  const values = [
    {
      icon: Users,
      title: "Community First",
      description: "Building meaningful connections through shared experiences and memorable events"
    },
    {
      icon: Target,
      title: "Innovation",
      description: "Leveraging cutting-edge technology to simplify event discovery and management"
    },
    {
      icon: Shield,
      title: "Trust & Security",
      description: "Ensuring safe, reliable, and transparent event experiences for everyone"
    },
    {
      icon: Heart,
      title: "Passion",
      description: "Driven by our love for bringing people together through amazing events"
    }
  ];



  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-muted/50">
      <section className="relative py-20 md:py-32 overflow-hidden">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-10 left-[10%] w-64 h-64 bg-primary/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '0s', animationDuration: '20s' }}></div>
          <div className="absolute top-20 right-[15%] w-96 h-96 bg-secondary/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '2s', animationDuration: '25s' }}></div>
          <div className="absolute bottom-20 left-[20%] w-80 h-80 bg-accent/10 rounded-full blur-3xl animate-float" style={{ animationDelay: '4s', animationDuration: '22s' }}></div>
          <div className="absolute top-1/2 right-[10%] w-72 h-72 bg-primary/8 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s', animationDuration: '18s' }}></div>
          
          <div className="absolute top-1/4 left-[30%] w-48 h-48 bg-secondary/15 rounded-full blur-2xl animate-float" style={{ animationDelay: '3s', animationDuration: '15s' }}></div>
          <div className="absolute bottom-1/4 right-[25%] w-56 h-56 bg-accent/12 rounded-full blur-2xl animate-float" style={{ animationDelay: '5s', animationDuration: '17s' }}></div>
          
          <div className="absolute top-1/3 right-[40%] w-32 h-32 bg-primary/20 rounded-full blur-xl animate-float" style={{ animationDelay: '2.5s', animationDuration: '12s' }}></div>
          <div className="absolute bottom-1/3 left-[35%] w-40 h-40 bg-secondary/18 rounded-full blur-xl animate-float" style={{ animationDelay: '4.5s', animationDuration: '14s' }}></div>
        </div>

        <div className="container mx-auto px-4 py-14 relative z-10">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <div>
              <span className="text-sm font-bold text-primary uppercase tracking-wider">About FuldaNexus</span>
            </div>

            <h1 className="text-4xl md:text-5xl lg:text-6xl font-bold leading-tight">
              Where Events Meet{" "}
              <span className="text-primary">Community</span>
            </h1>

            <p className="text-lg md:text-xl text-muted-foreground max-w-3xl mx-auto leading-relaxed">
              We're building more than a platform—we're creating a space where event organizers and attendees connect, share experiences, and build lasting memories together.
            </p>

            {/* <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-8">
              <div className="p-6 rounded-2xl bg-card/80 backdrop-blur-sm border border-border hover:border-primary/50 transition-all hover:scale-105">
                <div className="text-3xl font-bold text-primary mb-2">500+</div>
                <div className="text-sm text-muted-foreground">Events</div>
              </div>
              <div className="p-6 rounded-2xl bg-card/80 backdrop-blur-sm border border-border hover:border-secondary/50 transition-all hover:scale-105">
                <div className="text-3xl font-bold text-secondary mb-2">10K+</div>
                <div className="text-sm text-muted-foreground">Attendees</div>
              </div>
              <div className="p-6 rounded-2xl bg-card/80 backdrop-blur-sm border border-border hover:border-accent/50 transition-all hover:scale-105">
                <div className="text-3xl font-bold text-accent mb-2">50+</div>
                <div className="text-sm text-muted-foreground">Organizers</div>
              </div>
              <div className="p-6 rounded-2xl bg-card/80 backdrop-blur-sm border border-border hover:border-primary/50 transition-all hover:scale-105">
                <div className="text-3xl font-bold text-primary mb-2">84</div>
                <div className="text-sm text-muted-foreground">Cities</div>
              </div>
            </div> */}
          </div>
        </div>
      </section>
      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="grid md:grid-cols-2 gap-12 items-center max-w-6xl mx-auto">
            <div className="space-y-6">
              <h2 className="text-3xl md:text-4xl font-bold">
                What are the benefits of being at{" "}
                <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
                  FuldaNexus?
                </span>
              </h2>
              
              <ul className="space-y-4">
                {benefits.map((benefit, index) => (
                  <li key={index} className="flex items-start gap-3">
                    <CheckCircle2 className="w-5 h-5 text-primary mt-0.5 flex-shrink-0" />
                    <span className="text-muted-foreground">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="relative">
              <div className="aspect-square bg-gradient-to-br from-primary/20 to-secondary/20 rounded-3xl flex items-center justify-center p-8">
                <div className="text-center space-y-4">
                  <div className="w-24 h-24 mx-auto bg-gradient-to-br from-primary to-secondary rounded-full flex items-center justify-center shadow-2xl">
                    <Zap className="w-12 h-12 text-white" />
                  </div>
                  <h3 className="text-2xl font-bold">Seamless Experience</h3>
                  <p className="text-muted-foreground">
                    From discovery to attendance, we make every step effortless
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-br from-secondary/10 via-background to-primary/10">
        <div className="container mx-auto px-4">
          <div className="max-w-4xl mx-auto text-center space-y-8">
            <h2 className="text-3xl md:text-5xl font-bold">Our Vision</h2>
            
            <div className="space-y-6 text-lg text-muted-foreground leading-relaxed">
              <p>
                We see a world where finding the perfect event or hosting your gathering becomes a seamless and enjoyable experience.
              </p>
              
              <p>
                FuldaNexus is not just a platform; it's a commitment to redefine how you experience events, transforming the process into a journey of meaningful connections.
              </p>
              
              <p>
                We go beyond traditional transactions, aiming to make event participation more than just attendance but a meaningful and enriching connection with the experiences that matter most to you. Welcome to FuldaNexus, where we redefine events with a focus on seamless experiences and meaningful connections.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20">
        <div className="container mx-auto px-4">
          <div className="text-center max-w-3xl mx-auto mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">
              Our Core Values
            </h2>
            <p className="text-lg text-muted-foreground">
              The principles that guide everything we do
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
            {values.map((value, index) => {
              const Icon = value.icon;
              return (
                <Card key={index} className="text-center hover:shadow-xl transition-all hover:scale-105 border-primary/20">
                  <CardHeader>
                    <div className="w-16 h-16 mx-auto bg-gradient-to-br from-primary/20 to-secondary/20 rounded-2xl flex items-center justify-center mb-4">
                      <Icon className="w-8 h-8 text-primary" />
                    </div>
                    <CardTitle className="text-xl">{value.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-muted-foreground">{value.description}</p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-br from-primary/15 via-secondary/10 to-accent/15">
        <div className="container mx-auto px-4">
          <Card className="bg-gradient-to-br from-blue-50 via-sky-50 to-cyan-50 dark:from-blue-950/20 dark:via-sky-950/15 dark:to-cyan-950/20 border-primary/30 border-2 shadow-2xl overflow-hidden relative max-w-4xl mx-auto">
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(59,130,246,0.15),transparent_70%)]" />
            <CardContent className="py-16 text-center space-y-6 relative">
              <h2 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-primary via-secondary to-accent bg-clip-text text-transparent">
                Get Started with FuldaNexus
              </h2>
              <p className="text-lg text-foreground/80 max-w-2xl mx-auto">
                Join our community today and discover amazing events or start hosting your own
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-4">
                <Link to="/events">
                  <Button size="lg" className="w-full sm:w-auto shadow-xl hover:shadow-2xl hover:scale-105 transition-all duration-300">
                    Explore Events
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>
                <Link to="/register">
                  <Button size="lg" variant="outline" className="w-full sm:w-auto hover:bg-primary/5 hover:text-primary hover:border-primary/50 shadow-lg hover:shadow-xl hover:scale-105 transition-all duration-300">
                    Create Account
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </div>
  );
};

export default About;
